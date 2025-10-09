
import os, sys, math
import jax, jax.numpy as jnp
import triton
import triton.language as tl
import jax_triton as jt

@triton.jit
def add_kernel(x_ptr, y_ptr, length, out_ptr, BLOCK: tl.constexpr):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK
    offsets = block_start + tl.arange(0, BLOCK)
    mask = offsets < length
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)

def add_triton(x, y, block_size=128):
    assert x.shape == y.shape and x.ndim == 1
    n = x.size
    out_shape = jax.ShapeDtypeStruct(shape=x.shape, dtype=x.dtype)
    grid = (math.ceil(n / block_size),)
    return jt.triton_call(x, y, n, kernel=add_kernel, out_shape=out_shape, grid=grid, BLOCK=block_size)

@jax.jit
def add_jit(x,y): return add_triton(x,y)

def main():
    x = jnp.arange(10**6, dtype=jnp.float32)
    y = 2*jnp.ones_like(x)
    z = add_jit(x,y).block_until_ready()
    ok = jnp.allclose(z, x+y, rtol=1e-6, atol=1e-6)
    print("backend:", jax.default_backend())
    print("size:", x.size)
    print("first_values:", z[:5])
    print("result:", "PASS" if bool(ok) else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
