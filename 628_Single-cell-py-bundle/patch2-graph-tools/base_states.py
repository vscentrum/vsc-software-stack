#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# graph_tool -- a general graph manipulation python module
#
# Copyright (C) 2006-2025 Tiago de Paula Peixoto <tiago@skewed.de>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from .. import Vector_size_t, group_vector_property, _parallel

from . util import *

import functools
from abc import ABC, abstractmethod
import inspect
import functools
import textwrap
import math
import numpy

__test__ = False

def set_test(test):
    global __test__
    __test__ = test

def _bm_test():
    global __test__
    return __test__

def copy_state_wrap(func):
    @functools.wraps(func)
    def wrapper(self, *args, test=True, **kwargs):

        S = func(self, *args, **kwargs)

        if _bm_test() and test:
            assert not numpy.isnan(S) and not numpy.isinf(S), \
                "invalid entropy %g (%s) " % (S, str(args))

            state_copy = self.copy()
            Salt = state_copy.entropy(*args, test=False, **kwargs)

            assert math.isclose(S, Salt, abs_tol=1e-8), \
                "entropy discrepancy after copying (%g %g %g)" % (S, Salt,
                                                                  S - Salt)
        return S

    return wrapper

def mcmc_sweep_wrap(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        test = kwargs.pop("test", True)
        entropy_args = kwargs.get("entropy_args", {})

        if not kwargs.get("dispatch", True):
            return func(self, *args, **kwargs)

        if _bm_test() and test:
            if hasattr(self, "_check_clabel"):
                assert self._check_clabel(), "invalid clabel before sweep"
            Si = self.entropy(**entropy_args)

        ret = func(self, *args, **kwargs)

        if _bm_test() and test:
            if hasattr(self, "_check_clabel"):
                assert self._check_clabel(), "invalid clabel after sweep"
            dS = ret[0]
            Sf = self.entropy(**entropy_args)
            assert math.isclose(dS, (Sf - Si), abs_tol=1e-8), \
                "inconsistent entropy delta %g (%g): %s" % (dS, Sf - Si,
                                                            str(entropy_args))
        return ret
    return wrapper

def entropy_state_signature(cls):
    def entropy(self, **kwargs):
        return self._entropy(**dict(self.get_entropy_args(), **kwargs))
    entropy.__signature__ = inspect.signature(cls._entropy)
    intro, br, rest = cls._entropy.__doc__.partition("\n\n")
    warn = f"""\
    The default arguments of this function are overriden by those
    obtained from :meth:`~{cls.__name__}.get_entropy_args`. To update the
    defaults in a stateful way, :meth:`~{cls.__name__}.update_entropy_args`
    should be called."""
    warn = textwrap.dedent(warn)
    warn = " ".join(warn.splitlines())
    warn = textwrap.fill(warn, width=60, break_long_words=False,
                         replace_whitespace=False)
    warn = f".. warning::\n{warn}"
    lines = cls._entropy.__doc__.splitlines()
    m = min((len(l) - len(l.lstrip()) for l in lines[1:] if l.lstrip() != "")) \
        if len(lines) > 1 else 0
    warn = "\n".join([" " * (m if j == 0 else m + 4) + l.lstrip() for
                      j, l in enumerate(warn.splitlines())])
    entropy.__doc__ = intro + "\n\n" + warn
    if len(rest) > 0:
        entropy.__doc__ += "\n\n" + rest
    setattr(cls, "entropy", entropy)
    cls.get_entropy_args.__doc__ = \
        cls.get_entropy_args.__doc__.replace("{entropy}",
                                             f":meth:`~{cls.__name__}.entropy`")
    cls.update_entropy_args.__doc__ = \
        cls.update_entropy_args.__doc__.replace("{entropy}",
                                                f":meth:`~{cls.__name__}.entropy`")
    cls.reset_entropy_args.__doc__ = \
        cls.reset_entropy_args.__doc__.replace("{entropy}",
                                               f":meth:`~{cls.__name__}.entropy`")
    return cls

class EntropyState(ABC):
    r"""Base state that implements entropy arguments."""

    def __init__(self, entropy_args={}):
        self._entropy_args = {}
        self.reset_entropy_args()
        self._entropy_args.update(entropy_args)

    def get_entropy_args(self):
        """Return the current default values for the parameters of the function
        {entropy}, together with other operations that depend on them.
        """
        return self._entropy_args.copy()

    def update_entropy_args(self, **kwargs):
        """Update the default values for the parameters of the function
        {entropy} from the keyword arguments, in a stateful way, together with
        other operations that depend on them.

        Values updated in this manner are preserved by the copying or pickling
        of the state.
        """
        for k, v in kwargs.items():
            if k not in self._entropy_args:
                raise ValueError(f"unrecognized entropy argument: {k}")
            self._entropy_args[k] = v

    def reset_entropy_args(self):
        """Reset the current default values for the parameters of the function
        {entropy}, together with other operations that depend on them.
        """
        sig = inspect.signature(self._entropy)
        for k, v in sig.parameters.items():
            if k in ["self", "kwargs"]:
                continue
            self._entropy_args[k] = v.default

    def __getstate__(self):
        eargs = self.get_entropy_args()
        sig = inspect.signature(self.entropy)
        for k, v in sig.parameters.items():
            if k in eargs and eargs[k] == v:
                eargs.pop(k)
        return dict(entropy_args=eargs)

    @abstractmethod
    def _entropy(self, **kwargs):
        pass

    @abstractmethod
    def _gen_eargs(self, args):
        pass

    def _get_entropy_args(self, eargs, consume=False):
        if not consume:
            eargs = dict(self._entropy_args, **eargs)
        ea = self._gen_eargs(eargs)
        for arg in list(eargs.keys()):
            if arg not in self._entropy_args:
                continue
            setattr(ea, arg, eargs.pop(arg, self._entropy_args[arg]))
        for k in ["self", "kwargs"]:
            eargs.pop(k, None)
        if len(eargs) > 0 and not consume:
            raise ValueError("unrecognized entropy arguments: " +
                             str(list(eargs.keys())))
        return ea


class MCMCState(EntropyState):
    r"""Base state that implements single-flip MCMC sweeps."""

    @abstractmethod
    def _mcmc_sweep_dispatch(self, mcmc_state):
        pass

    @mcmc_sweep_wrap
    def mcmc_sweep(self, beta=1., c=.5, d=.01, niter=1, entropy_args={},
                   allow_vacate=True, sequential=True, deterministic=False,
                   vertices=None, verbose=False, **kwargs):
        r"""Perform ``niter`` sweeps of a Metropolis-Hastings acceptance-rejection
        MCMC to sample network partitions.

        Parameters
        ----------
        beta : ``float`` (optional, default: ``1.``)
            Inverse temperature.
        c : ``float`` (optional, default: ``.5``)
            Sampling parameter ``c`` for move proposals: For :math:`c\to 0` the
            blocks are sampled according to the local neighborhood of a given
            node and their block connections; for :math:`c\to\infty` the blocks
            are sampled randomly. Note that only for :math:`c > 0` the MCMC is
            guaranteed to be ergodic.
        d : ``float`` (optional, default: ``.01``)
            Probability of selecting a new (i.e. empty) group for a given move.
        niter : ``int`` (optional, default: ``1``)
            Number of sweeps to perform. During each sweep, a move attempt is
            made for each node.
        entropy_args : ``dict`` (optional, default: ``{}``)
            Entropy arguments, with the same meaning and defaults as in
            :meth:`graph_tool.inference.BlockState.entropy`.
        allow_vacate : ``bool`` (optional, default: ``True``)
            Allow groups to be vacated.
        sequential : ``bool`` (optional, default: ``True``)
            If ``sequential == True`` each vertex move attempt is made
            sequentially, where vertices are visited in random order. Otherwise
            the moves are attempted by sampling vertices randomly, so that the
            same vertex can be moved more than once, before other vertices had
            the chance to move.
        deterministic : ``bool`` (optional, default: ``False``)
            If ``sequential == True`` and ``deterministic == True`` the
            vertices will be visited in deterministic order.
        vertices : ``list`` of ints (optional, default: ``None``)
            If provided, this should be a list of vertices which will be
            moved. Otherwise, all vertices will.
        verbose : ``bool`` (optional, default: ``False``)
            If ``verbose == True``, detailed information will be displayed.

        Returns
        -------
        dS : ``float``
            Entropy difference after the sweeps.
        nattempts : ``int``
            Number of vertex moves attempted.
        nmoves : ``int``
            Number of vertices moved.

        Notes
        -----
        This algorithm has an :math:`O(E)` complexity, where :math:`E` is the
        number of edges (independent of the number of groups).

        References
        ----------
        .. [peixoto-efficient-2014] Tiago P. Peixoto, "Efficient Monte Carlo and
           greedy heuristic for the inference of stochastic block models", Phys.
           Rev. E 89, 012804 (2014), :doi:`10.1103/PhysRevE.89.012804`,
           :arxiv:`1310.4378`
        """

        mcmc_state = DictState(locals())
        mcmc_state.entropy_args = self._get_entropy_args(entropy_args)
        mcmc_state.vlist = Vector_size_t()
        if vertices is None:
            vertices = self.g.vertex_index.copy().fa
            if getattr(self, "is_weighted", False):
                # ignore vertices with zero weight
                vw = self.vweight.fa
                vertices = vertices[vw > 0]
        mcmc_state.vlist.resize(len(vertices))
        mcmc_state.vlist.a = vertices
        mcmc_state.state = self._state

        dispatch = kwargs.pop("dispatch", True)

        if len(kwargs) > 0:
            raise ValueError("unrecognized keyword arguments: " +
                             str(list(kwargs.keys())))
        if dispatch:
            return self._mcmc_sweep_dispatch(mcmc_state)
        else:
            return mcmc_state

class MultiflipMCMCState(EntropyState):
    r"""Base state that implements multiflip (merge-split) MCMC sweeps."""

    @abstractmethod
    def _multiflip_mcmc_sweep_dispatch(self, mcmc_state):
        pass

    @mcmc_sweep_wrap
    def multiflip_mcmc_sweep(self, beta=1., c=.5, psingle=None, psplit=1,
                             pmerge=1, pmergesplit=1, pmovelabel=0, d=0.01,
                             gibbs_sweeps=10, niter=1, entropy_args={},
                             accept_stats=None, verbose=False, **kwargs):
        r"""Perform ``niter`` sweeps of a Metropolis-Hastings acceptance-rejection MCMC
        with multiple simultaneous moves (i.e. merges and splits) to sample
        network partitions.

        Parameters
        ----------
        beta : ``float`` (optional, default: ``1.``)
            Inverse temperature.
        c : ``float`` (optional, default: ``.5``)
            Sampling parameter ``c`` for move proposals: For :math:`c\to 0` the
            blocks are sampled according to the local neighborhood of a given
            node and their block connections; for :math:`c\to\infty` the blocks
            are sampled randomly. Note that only for :math:`c > 0` the MCMC is
            guaranteed to be ergodic.
        psingle : ``float`` (optional, default: ``None``)
            Relative probability of proposing a single node move. If ``None``,
            it will be selected as the number of nodes in the graph.
        psplit : ``float`` (optional, default: ``1``)
            Relative probability of proposing a group split.
        pmerge : ``float`` (optional, default: ``1``)
            Relative probability of proposing a group merge.
        pmergesplit : ``float`` (optional, default: ``1``)
            Relative probability of proposing a marge-split move.
        pmovelabel : ``float`` (optional, default: ``0``)
            Relative probability of proposing a group label move.
        d : ``float`` (optional, default: ``1``)
            Probability of selecting a new (i.e. empty) group for a given
            single-node move.
        gibbs_sweeps : ``int`` (optional, default: ``10``)
            Number of sweeps of Gibbs sampling to be performed (i.e. each node
            is attempted once per sweep) to refine a split proposal.
        niter : ``int`` (optional, default: ``1``)
            Number of sweeps to perform. During each sweep, a move attempt is
            made for each node, on average.
        entropy_args : ``dict`` (optional, default: ``{}``)
            Entropy arguments, with the same meaning and defaults as in
            :meth:`graph_tool.inference.BlockState.entropy`.
        accept_stats : ``dict`` (optional, default: ``None``)
            If provided, this dictionary will be updated with the proposal and
            acceptance counts for each kind of move.
        verbose : ``bool`` (optional, default: ``False``)
            If ``verbose == True``, detailed information will be displayed.

        Returns
        -------
        dS : ``float``
            Entropy difference after the sweeps.
        nattempts : ``int``
            Number of vertex moves attempted.
        nmoves : ``int``
            Number of vertices moved.

        Notes
        -----
        This algorithm has an :math:`O(E)` complexity, where :math:`E` is the
        number of edges (independent of the number of groups).

        References
        ----------
        .. [peixoto-merge-split-2020] Tiago P. Peixoto, "Merge-split Markov
           chain Monte Carlo for community detection", Phys. Rev. E 102, 012305
           (2020), :doi:`10.1103/PhysRevE.102.012305`, :arxiv:`2003.07070`

        """

        if psingle is None:
            psingle = self.g.num_vertices()
        gibbs_sweeps = max((gibbs_sweeps, 1))
        nproposal = Vector_size_t(4)
        nacceptance = Vector_size_t(4)
        force_move = kwargs.pop("force_move", False)
        mcmc_state = DictState(locals())
        mcmc_state.entropy_args = self._get_entropy_args(entropy_args)
        mcmc_state.state = self._state

        dispatch = kwargs.pop("dispatch", True)

        if len(kwargs) > 0:
            raise ValueError("unrecognized keyword arguments: " +
                             str(list(kwargs.keys())))
        if dispatch:
            dS, nattempts, nmoves = self._multiflip_mcmc_sweep_dispatch(mcmc_state)
        else:
            return mcmc_state

        if accept_stats is not None:
            for key in ["proposal", "acceptance"]:
                if key not in accept_stats:
                    accept_stats[key] = numpy.zeros(len(nproposal),
                                                    dtype="uint64")
            accept_stats["proposal"] += nproposal.a
            accept_stats["acceptance"] += nacceptance.a

        return dS, nattempts, nmoves

class MultilevelMCMCState(EntropyState):
    r"""Base state that implements multilevel agglomerative MCMC sweeps."""

    @abstractmethod
    def _multilevel_mcmc_sweep_dispatch(self, mcmc_state):
        pass

    def _get_bclabel(self):
        return None

    @mcmc_sweep_wrap
    def multilevel_mcmc_sweep(self, niter=1, beta=numpy.inf, c=.5, d=0.01, r=0.9,
                              random_bisect=True, merge_sweeps=10, mh_sweeps=10,
                              init_r=0.99, init_min_iter=5, init_beta=1.,
                              gibbs=False, B_min=1,
                              B_max=numpy.iinfo(numpy.uint64).max, b_min=None,
                              b_max=None, M=None, cache_states=True,
                              force_accept=False, parallel=False,
                              entropy_args={}, verbose=False, **kwargs):
        r"""Perform ``niter`` sweeps of a multilevel agglomerative
        acceptance-rejection pseudo-MCMC (i.e. detailed balance is not
        preserved) to sample network partitions, that uses a bisection search on
        the number of groups, together with group merges and singe-node moves.

        Parameters
        ----------
        niter : ``int`` (optional, default: ``1``)
            Number of sweeps to perform. During each sweep, a move attempt is
            made for each node, on average.
        beta : ``float`` (optional, default: :const:`numpy.inf`)
            Inverse temperature.
        c : ``float`` (optional, default: ``.5``)
            Sampling parameter ``c`` for move proposals: For :math:`c\to 0` the
            blocks are sampled according to the local neighborhood of a given
            node and their block connections; for :math:`c\to\infty` the blocks
            are sampled randomly. Note that only for :math:`c > 0` the MCMC is
            guaranteed to be ergodic.
        d : ``float`` (optional, default: ``.01``)
            Probability of selecting a new (i.e. empty) group for a given
            single-node move.
        r : ``float`` (optional, default: ``0.9``)
            Group shrink ratio. The number of groups is reduced by this fraction
            at each merge sweep.
        random_bisect : ``bool`` (optional, default: ``True``)
            If ``True``, bisections are done at randomly chosen
            intervals. Otherwise a Fibonacci sequence is used.
        merge_sweeps : ``int`` (optional, default: ``10``)
            Number of sweeps spent to find good merge proposals.
        mh_sweeps : ``int`` (optional, default: ``10``)
            Number of single-node Metropolis-Hastings sweeps between merge splits.
        init_r : ``double`` (optional, default: ``0.99``)
            Stopping criterion for the intialization phase, after each node is
            put in their own group, to set the initial upper bound of the
            bisection search. A number of single-node Metropolis-Hastings sweeps
            is done until the number of groups is shrunk by a factor that is
            larger than this parameter.
        init_min_iter : ``int`` (optional, default: ``5``)
            Minimum number of iterations at the intialization phase.
        init_beta : ``float`` (optional, default: ``1.``)
            Inverse temperature to be used for the very first sweep of the
            initialization phase.
        gibbs : ``bool`` (optional, default: ``False``)
            If ``True``, the single node moves use (slower) Gibbs sampling,
            rather than Metropolis-Hastings.
        B_min : ``int`` (optional, default: ``1``)
            Minimum number of groups to be considered in the search.
        b_min : :class:`~graph_tool.VertexPropertyMap` (optional, default: ``None``)
            If provided, this will be used for the partition corresponding to ``B_min``.
        B_max : ``int`` (optional, default: ``numpy.iinfo(numpy.uint64).max``)
            Maximum number of groups to be considered in the search.
        b_max : :class:`~graph_tool.VertexPropertyMap` (optional, default: ``None``)
            If provided, this will be used for the partition corresponding to ``B_max``.
        M : ``int`` (optional, default: ``None``)
            Maximum number of groups to select for the multilevel move. If
            ``None`` is provided, then all groups are always elected.
        cache_states : ``bool`` (optional, default: ``True``)
            If ``True``, intermediary states will be cached during the bisection
            search.
        force_accept : ``bool`` (optional, default: ``False``)
            If ``True``, new state will be accepted even if it does not improve
            the objective function.
        parallel : ``bool`` (optional, default: ``False``)
            If ``True``, the algorithm will run in parallel (if enabled during
            compilation).
        entropy_args : ``dict`` (optional, default: ``{}``)
            Entropy arguments, with the same meaning and defaults as in
            :meth:`graph_tool.inference.BlockState.entropy`.
        verbose : ``bool`` (optional, default: ``False``)
            If ``verbose == True``, detailed information will be displayed.

        Returns
        -------
        dS : ``float``
            Entropy difference after the sweeps.
        nattempts : ``int``
            Number of vertex moves attempted.
        nmoves : ``int``
            Number of vertices moved.

        Notes
        -----
        This algorithm has an :math:`O(E\ln^2 N)` complexity, where :math:`E` is
        the number of edges and :math:`N` is the number of nodes (independently of
        the number of groups).

        References
        ----------
        .. [peixoto-efficient-2014] Tiago P. Peixoto, "Efficient Monte Carlo and
           greedy heuristic for the inference of stochastic block models", Phys.
           Rev. E 89, 012804 (2014), :doi:`10.1103/PhysRevE.89.012804`,
           :arxiv:`1310.4378`

        """

        merge_sweeps = max((merge_sweeps, 1))
        if M is None:
            M = self.g.num_vertices()
            global_moves = True
        else:
            global_moves = False
        bclabel = self._get_bclabel()
        if bclabel is not None:
            B_min = max((len(numpy.unique(bclabel.fa)), B_min))
        if b_min is None:
            b_min = self.g.vertex_index.copy("int64_t")
        if b_max is None:
            b_max = self.g.new_vp("int64_t")

        mcmc_state = DictState(locals())
        mcmc_state.entropy_args = self._get_entropy_args(entropy_args)
        mcmc_state.state = self._state

        dispatch = kwargs.pop("dispatch", True)

        if len(kwargs) > 0:
            raise ValueError("unrecognized keyword arguments: " +
                             str(list(kwargs.keys())))
        if dispatch:
            return self._multilevel_mcmc_sweep_dispatch(mcmc_state)
        else:
            return mcmc_state

class GibbsMCMCState(EntropyState):
    r"""Base state that implements single flip MCMC sweeps."""

    @abstractmethod
    def _gibbs_sweep_dispatch(self, gibbs_state):
        pass

    @mcmc_sweep_wrap
    def gibbs_sweep(self, beta=1., niter=1, entropy_args={},
                    allow_new_group=True, sequential=True, deterministic=False,
                    vertices=None, verbose=False, **kwargs):
        r"""Perform ``niter`` sweeps of a rejection-free Gibbs MCMC to sample network
        partitions.

        Parameters
        ----------
        beta : ``float`` (optional, default: ``1.``)
            Inverse temperature.
        niter : ``int`` (optional, default: ``1``)
            Number of sweeps to perform. During each sweep, a move attempt is
            made for each node.
        entropy_args : ``dict`` (optional, default: ``{}``)
            Entropy arguments, with the same meaning and defaults as in
            :meth:`graph_tool.inference.BlockState.entropy`.
        allow_new_group : ``bool`` (optional, default: ``True``)
            Allow the number of groups to increase and decrease.
        sequential : ``bool`` (optional, default: ``True``)
            If ``sequential == True`` each vertex move attempt is made
            sequentially, where vertices are visited in random order. Otherwise
            the moves are attempted by sampling vertices randomly, so that the
            same vertex can be moved more than once, before other vertices had
            the chance to move.
        deterministic : ``bool`` (optional, default: ``False``)
            If ``sequential == True`` and ``deterministic == True`` the
            vertices will be visited in deterministic order.
        vertices : ``list`` of ints (optional, default: ``None``)
            If provided, this should be a list of vertices which will be
            moved. Otherwise, all vertices will.
        verbose : ``bool`` (optional, default: ``False``)
            If ``verbose == True``, detailed information will be displayed.

        Returns
        -------
        dS : ``float``
            Entropy difference after the sweeps.
        nattempts : ``int``
            Number of vertex moves attempted.
        nmoves : ``int``
            Number of vertices moved.

        Notes
        -----
        This algorithm has an :math:`O(E\times B)` complexity, where :math:`B`
        is the number of groups, and :math:`E` is the number of edges.

        """

        gibbs_state = DictState(locals())
        gibbs_state.entropy_args = self._get_entropy_args(entropy_args)
        gibbs_state.vlist = Vector_size_t()
        if vertices is None:
            vertices = self.g.get_vertices()
        gibbs_state.vlist.resize(len(vertices))
        gibbs_state.vlist.a = vertices
        gibbs_state.state = self._state

        if len(kwargs) > 0:
            raise ValueError("unrecognized keyword arguments: " +
                             str(list(kwargs.keys())))

        dS, nattempts, nmoves = self._gibbs_sweep_dispatch(gibbs_state)

        return dS, nattempts, nmoves

class MulticanonicalMCMCState(EntropyState):
    r"""Base state that implements multicanonical MCMC sweeps."""

    @abstractmethod
    def _multicanonical_sweep_dispatch(self, multicanonical_state):
        pass

    @mcmc_sweep_wrap
    def multicanonical_sweep(self, m_state, multiflip=False, **kwargs):
        r"""Perform ``niter`` sweeps of a non-Markovian multicanonical sampling using the
        Wang-Landau algorithm.

        Parameters
        ----------
        m_state : :class:`~graph_tool.inference.MulticanonicalState`
            :class:`~graph_tool.inference.MulticanonicalState` instance
            containing the current state of the Wang-Landau run.
        multiflip : ``bool`` (optional, default: ``False``)
            If ``True``, ``multiflip_mcmc_sweep()`` will be used, otherwise
            ``mcmc_sweep()``.
        **kwargs : Keyword parameter list
            The remaining parameters will be passed to
            ``multiflip_mcmc_sweep()`` or ``mcmc_sweep()``.

        Returns
        -------
        dS : ``float``
            Entropy difference after the sweeps.
        nattempts : ``int``
            Number of vertex moves attempted.
        nmoves : ``int``
            Number of vertices moved.

        Notes
        -----
        This algorithm has an :math:`O(E)` complexity, where :math:`E` is the
        number of edges (independent of the number of groups).

        References
        ----------
        .. [wang-efficient-2001] Fugao Wang, D. P. Landau, "An efficient, multiple
           range random walk algorithm to calculate the density of states", Phys.
           Rev. Lett. 86, 2050 (2001), :doi:`10.1103/PhysRevLett.86.2050`,
           :arxiv:`cond-mat/0011174`
        """

        if not multiflip:
            kwargs["sequential"] = False
        kwargs["beta"] = 1

        args = dmask(locals(), ["self", "kwargs"])
        multi_state = DictState(args)

        entropy_args = kwargs.get("entropy_args", {})
        entropy_offset = kwargs.pop("entropy_offset", 0)

        if multiflip:
            mcmc_state = self.multiflip_mcmc_sweep(dispatch=False, **kwargs)
        else:
            mcmc_state = self.mcmc_sweep(dispatch=False, **kwargs)

        multi_state.update(mcmc_state)
        multi_state.multiflip = multiflip

        multi_state.S = self.entropy(**entropy_args) + entropy_offset
        multi_state.state = self._state

        multi_state.f = m_state._f
        multi_state.S_min = m_state._S_min
        multi_state.S_max = m_state._S_max
        multi_state.hist = m_state._hist
        multi_state.dens = m_state._density

        if (multi_state.S < multi_state.S_min or
            multi_state.S > multi_state.S_max):
            raise ValueError("initial entropy %g out of bounds (%g, %g)" %
                             (multi_state.S, multi_state.S_min,
                              multi_state.S_max))

        S, nattempts, nmoves = self._multicanonical_sweep_dispatch(multi_state)

        return S, nattempts, nmoves

class ExhaustiveSweepState(EntropyState):
    r"""Base state that implements exhaustive enumerative sweeps."""

    @abstractmethod
    def _exhaustive_sweep_dispatch(self, exhaustive_state):
        pass

    def exhaustive_sweep(self, entropy_args={}, callback=None, density=None,
                         vertices=None, initial_partition=None, max_iter=None):
        r"""Perform an exhaustive loop over all possible network partitions.

        Parameters
        ----------
        entropy_args : ``dict`` (optional, default: ``{}``)
            Entropy arguments, with the same meaning and defaults as in
            :meth:`graph_tool.inference.BlockState.entropy`.
        callback : callable object (optional, default: ``None``)
            Function to be called for each partition, with three arguments ``(S,
            S_min, b_min)`` corresponding to the the current entropy value, the
            minimum entropy value so far, and the corresponding partition,
            respectively. If not provided, and ``hist is None`` an iterator over
            the same values will be returned instead.
        density : ``tuple`` (optional, default: ``None``)
            If provided, it should contain a tuple with values ``(S_min, S_max,
            n_bins)``, which will be used to obtain the density of states via a
            histogram of size ``n_bins``. This parameter is ignored unless
            ``callback is None``.
        vertices : iterable of ints (optional, default: ``None``)
            If provided, this should be a list of vertices which will be
            moved. Otherwise, all vertices will.
        initial_partition : iterable  of ints (optional, default: ``None``)
            If provided, this will provide the initial partition for the
            iteration.
        max_iter : ``int`` (optional, default: ``None``)
            If provided, this will limit the total number of iterations.

        Returns
        -------
        states : iterator over (S, S_min, b_min)
            If ``callback`` is ``None`` and ``hist`` is ``None``, the function
            will return an iterator over ``(S, S_min, b_min)`` corresponding to
            the the current entropy value, the minimum entropy value so far, and
            the corresponding partition, respectively.
        Ss, counts : pair of :class:`numpy.ndarray`
            If ``callback is None`` and ``hist is not None``, the function will
            return the values of each bin (``Ss``) and the state count of each
            bin (``counts``).
        b_min : :class:`~graph_tool.VertexPropertyMap`
            If ``callback is not None`` or ``hist is not None``, the function
            will also return partition with smallest entropy.

        Notes
        -----

        This algorithm has an :math:`O(B^N)` complexity, where :math:`B` is the
        number of groups, and :math:`N` is the number of vertices.

        """

        exhaustive_state = DictState(dict(max_iter=max_iter if max_iter is not None else 0))
        exhaustive_state.entropy_args = self._get_entropy_args(entropy_args)
        exhaustive_state.vlist = Vector_size_t()
        if vertices is None:
            vertices = self.g.vertex_index.copy().fa
            if getattr(self, "is_weighted", False):
                # ignore vertices with zero weight
                vw = self.vweight.fa
                vertices = vertices[vw > 0]
        if initial_partition is None:
            initial_partition = zeros(len(vertices), dtype="uint64")
        self.move_vertex(vertices, initial_partition)
        exhaustive_state.vlist.resize(len(vertices))
        exhaustive_state.vlist.a = vertices
        exhaustive_state.S = self.entropy(**entropy_args)
        exhaustive_state.state = self._state
        exhaustive_state.b_min = b_min = self.g.new_vp("int32_t")

        if density is not None:
            density = (density[0], density[1],
                       numpy.zeros(density[2], dtype="uint64"))
        if callback is not None:
            _callback = lambda S, S_min: callback(S, S_min, b_min)
        else:
            _callback = None
        ret = self._exhaustive_sweep_dispatch(exhaustive_state, _callback,
                                              density)
        if _callback is None:
            if density is None:
                return ((S, S_min, b_min) for S, S_min in ret)
            else:
                Ss = numpy.linspace(density[0], density[1], len(density[2]))
                return (Ss, density[2]), b_min
        else:
            return b_min

class DrawBlockState(ABC):
    r"""Base state that implements group-based drawing."""

    def draw(self, **kwargs):
        r"""Convenience wrapper to :func:`~graph_tool.draw.graph_draw` that
        draws the state of the graph as colors on the vertices and edges."""
        import graph_tool.draw
        gradient = self.g.new_ep("double")
        gradient = group_vector_property([gradient])
        b = self.g.own_property(self.b)
        return graph_tool.draw.graph_draw(self.g,
                                          vertex_fill_color=kwargs.pop("vertex_fill_color", b),
                                          vertex_color=kwargs.pop("vertex_color", b),
                                          edge_gradient=kwargs.pop("edge_gradient", gradient),
                                          vcmap=kwargs.pop("vcmap", graph_tool.draw.default_cm),
                                          **kwargs)
