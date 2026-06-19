#!/usr/bin/env bash
set -euo pipefail

# Avoid accidental CUDA/ROCm/oneAPI/PJRT plugin discovery on CPU-only installs.
export JAX_PLATFORMS=cpu

python - <<'PY'
import sys
import numpy as np

import jax
import jaxlib
import jax.numpy as jnp
from jax import grad, jit, vmap, lax, random

print("Python:", sys.version.split()[0])
print("jax:", jax.__version__)
print("jaxlib:", jaxlib.__version__)
print("default backend:", jax.default_backend())
print("devices:", jax.devices())

assert jax.__version__ == "0.10.1", jax.__version__
assert jaxlib.__version__ == "0.10.1", jaxlib.__version__
assert jax.default_backend() == "cpu", jax.default_backend()
assert len(jax.devices()) >= 1

# Basic JAX NumPy
x = jnp.arange(12, dtype=jnp.float32).reshape(3, 4)
y = jnp.sin(x) + jnp.cos(x)
assert y.shape == (3, 4)
assert np.isfinite(np.asarray(y)).all()

# JIT compilation
@jit
def matmul_plus_one(a, b):
    return a @ b + 1.0

a = jnp.arange(6, dtype=jnp.float32).reshape(2, 3)
b = jnp.arange(12, dtype=jnp.float32).reshape(3, 4)
out = matmul_plus_one(a, b)
expected = np.asarray(a) @ np.asarray(b) + 1.0
np.testing.assert_allclose(np.asarray(out), expected, rtol=1e-5, atol=1e-5)
print("jit matmul: OK")

# grad
def f(t):
    return jnp.sum(jnp.sin(t) * t)

g = grad(f)(jnp.array([0.1, 0.2, 0.3], dtype=jnp.float32))
expected_g = np.sin(np.array([0.1, 0.2, 0.3], dtype=np.float32)) + np.array([0.1, 0.2, 0.3], dtype=np.float32) * np.cos(np.array([0.1, 0.2, 0.3], dtype=np.float32))
np.testing.assert_allclose(np.asarray(g), expected_g, rtol=1e-5, atol=1e-5)
print("grad: OK")

# vmap
def square_plus_one(z):
    return z * z + 1

vmapped = vmap(square_plus_one)(jnp.arange(5, dtype=jnp.float32))
np.testing.assert_allclose(np.asarray(vmapped), np.arange(5, dtype=np.float32) ** 2 + 1)
print("vmap: OK")

# lax.scan
def body(carry, item):
    new_carry = carry + item
    return new_carry, new_carry

final, hist = lax.scan(body, 0, jnp.arange(5))
assert int(final) == 10
np.testing.assert_array_equal(np.asarray(hist), np.array([0, 1, 3, 6, 10]))
print("lax.scan: OK")

# random
key = random.PRNGKey(123)
samples = random.normal(key, (1000,), dtype=jnp.float32)
assert samples.shape == (1000,)
assert np.isfinite(np.asarray(samples)).all()
print("random: OK")

# linear algebra
m = jnp.array([[3.0, 1.0], [1.0, 2.0]], dtype=jnp.float32)
eigvals = jnp.linalg.eigvalsh(m)
np.testing.assert_allclose(np.asarray(eigvals), np.linalg.eigvalsh(np.asarray(m)), rtol=1e-5, atol=1e-5)
print("linalg: OK")

# Optional pmap check; only meaningful with multiple local CPU devices.
if jax.local_device_count() >= 2:
    from jax import pmap
    xs = jnp.arange(jax.local_device_count(), dtype=jnp.float32)
    ys = pmap(lambda z: z + 1)(xs)
    np.testing.assert_allclose(np.asarray(ys), np.asarray(xs) + 1)
    print("pmap: OK")
else:
    print("pmap: skipped, only one local device")

print("JAX smoke test passed")
PY