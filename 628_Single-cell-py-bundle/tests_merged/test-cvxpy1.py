#!/usr/bin/env python3

from importlib.metadata import PackageNotFoundError, version as pkg_version

import numpy as np
import scipy
import scipy.sparse as sp

import cvxpy as cp
import osqp
import qdldl


def dist_version(name):
    try:
        return pkg_version(name)
    except PackageNotFoundError:
        return "unknown"


def check_close(got, expected, tol=1e-6, label="value"):
    got = np.asarray(got, dtype=float)
    expected = np.asarray(expected, dtype=float)
    err = np.max(np.abs(got - expected))
    if err > tol:
        raise AssertionError(f"{label} mismatch: got {got}, expected {expected}, max_abs_err={err}")


def check_status(status, label):
    s = str(status).lower()
    if not s.startswith("solved") and s not in ("optimal",):
        raise AssertionError(f"{label} unexpected status: {status}")


def native_osqp_test():
    print("== Native OSQP test ==")

    P = sp.csc_matrix([[4.0, 0.0],
                       [0.0, 2.0]])
    A = sp.eye(2, format="csc")
    l = np.array([0.0, 0.0])
    u = np.array([1.0, 1.0])

    q1 = np.array([-4.0, -1.0])
    q2 = np.array([-2.0, -0.5])

    solver = osqp.OSQP()
    solver.setup(
        P=P, q=q1, A=A, l=l, u=u,
        verbose=False,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=20000,
        polish=True,
    )

    res1 = solver.solve()
    check_status(res1.info.status, "native OSQP solve #1")
    check_close(res1.x, [1.0, 0.5], label="native OSQP x #1")

    solver.update(q=q2)
    res2 = solver.solve()
    check_status(res2.info.status, "native OSQP solve #2")
    check_close(res2.x, [0.5, 0.25], label="native OSQP x #2")

    print("native OSQP: OK")


def cvxpy_osqp_test():
    print("== CVXPY -> OSQP test ==")

    installed = cp.installed_solvers()
    print("CVXPY installed solvers:", installed)
    if "OSQP" not in installed:
        raise AssertionError("CVXPY does not report OSQP as an installed solver")

    x = cp.Variable(2)
    q = cp.Parameter(2)

    P = np.array([[4.0, 0.0],
                  [0.0, 2.0]])

    constraints = [x >= 0, x <= 1]
    objective = cp.Minimize(0.5 * cp.quad_form(x, P) + q @ x)
    prob = cp.Problem(objective, constraints)

    if not prob.is_qp():
        raise AssertionError("Problem is not recognized by CVXPY as a QP")
    if not prob.is_dpp():
        raise AssertionError("Problem is not DPP; parameter-update path not exercised")

    q.value = np.array([-4.0, -1.0])
    val1 = prob.solve(
        solver=cp.OSQP,
        warm_start=True,
        verbose=False,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=20000,
    )
    if prob.status not in ("optimal", "optimal_inaccurate"):
        raise AssertionError(f"CVXPY/OSQP solve #1 failed with status {prob.status}")
    check_close(x.value, [1.0, 0.5], label="CVXPY/OSQP x #1")

    q.value = np.array([-2.0, -0.5])
    val2 = prob.solve(
        solver=cp.OSQP,
        warm_start=True,
        verbose=False,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=20000,
    )
    if prob.status not in ("optimal", "optimal_inaccurate"):
        raise AssertionError(f"CVXPY/OSQP solve #2 failed with status {prob.status}")
    check_close(x.value, [0.5, 0.25], label="CVXPY/OSQP x #2")

    solver_name = getattr(prob.solver_stats, "solver_name", "")
    if str(solver_name).upper() != "OSQP":
        raise AssertionError(f"CVXPY did not report OSQP as the solver, got {solver_name!r}")

    print("CVXPY -> OSQP: OK")
    print("objective values:", val1, val2)


def main():
    print("Versions:")
    print("  cvxpy :", cp.__version__)
    print("  osqp  :", getattr(osqp, "__version__", dist_version("osqp")))
    print("  qdldl :", getattr(qdldl, "__version__", dist_version("qdldl")))
    print("  numpy :", np.__version__)
    print("  scipy :", scipy.__version__)

    native_osqp_test()
    cvxpy_osqp_test()

    print("All CVXPY/OSQP tests passed.")


if __name__ == "__main__":
    main()