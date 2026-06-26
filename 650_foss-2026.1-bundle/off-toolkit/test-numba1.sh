#!/usr/bin/env bash
set -euo pipefail

export NUMBA_DISABLE_JIT=0
export NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-2}"

python -s <<'PY'
import os
import math
import numpy as np
import llvmlite
import llvmlite.binding as llvm
import numba
from numba import njit, prange, vectorize, guvectorize, float64
from numba.np.ufunc.parallel import get_num_threads, set_num_threads

print("Python executable:", os.sys.executable)
print("NumPy:", np.__version__)
print("llvmlite:", llvmlite.__version__)
print("LLVM:", llvm.llvm_version_info)
print("Numba:", numba.__version__)
print("NUMBA_NUM_THREADS:", os.environ.get("NUMBA_NUM_THREADS"))

@njit
def scalar_kernel(x):
    acc = 0.0
    for i in range(1000):
        acc += math.sin(x + i * 0.001) * math.cos(x - i * 0.002)
    return acc

ref = scalar_kernel.py_func(0.25)
got = scalar_kernel(0.25)
assert abs(got - ref) < 1e-10, (got, ref)
assert scalar_kernel.signatures, "scalar_kernel was not JIT-compiled"

@njit
def array_kernel(a):
    out = np.empty_like(a)
    for i in range(a.size):
        out[i] = a[i] * a[i] + 2.0 * a[i] + 1.0
    return out

a = np.linspace(-3.0, 3.0, 10000)
expected = a * a + 2.0 * a + 1.0
actual = array_kernel(a)
np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

set_num_threads(2)
assert get_num_threads() == 2, get_num_threads()

@njit(parallel=True)
def parallel_sum(a):
    total = 0.0
    for i in prange(a.size):
        total += a[i] * a[i]
    return total

psum = parallel_sum(a)
np.testing.assert_allclose(psum, np.sum(a * a), rtol=1e-10, atol=1e-10)

try:
    print("Threading layer:", numba.threading_layer())
except ValueError as err:
    raise AssertionError(f"Numba threading layer was not initialized: {err}")

@vectorize([float64(float64)], nopython=True)
def v_square_plus_one(x):
    return x * x + 1.0

np.testing.assert_allclose(v_square_plus_one(a), a * a + 1.0, rtol=1e-12, atol=1e-12)

@guvectorize([(float64[:], float64[:])], "(n)->(n)", nopython=True)
def g_scale(inp, out):
    for i in range(inp.shape[0]):
        out[i] = 3.0 * inp[i]

np.testing.assert_allclose(g_scale(a), 3.0 * a, rtol=1e-12, atol=1e-12)

print("Numba smoke test passed")
PY