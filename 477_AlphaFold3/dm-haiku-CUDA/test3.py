import time, numpy as np, jax, jax.numpy as jnp
print("JAX:", jax.__version__)
try:
    import jaxlib; print("jaxlib:", jaxlib.__version__)
except Exception: print("jaxlib: <unavailable>")
print("backend:", jax.default_backend())
print("devices:", [repr(d) for d in jax.devices()])

key0=jax.random.PRNGKey(0); key1=jax.random.PRNGKey(1)
A=jax.random.normal(key0,(512,512)); B=jax.random.normal(key1,(512,512))
f=lambda a,b: a@b+0.1
f_jit=jax.jit(f)
t0=time.time(); y0=f(A,B).block_until_ready(); t1=time.time()
t2=time.time(); y1=f_jit(A,B).block_until_ready(); t3=time.time()
print("matmul close:", bool(jnp.allclose(y0,y1))); print("times(s):", round(t1-t0,4), round(t3-t2,4))

loss=lambda x: jnp.square(jnp.sin(x)).sum()
g=jax.grad(loss); x=jnp.linspace(-3,3,1000); gx=g(x)
print("grad finite:", bool(jnp.isfinite(gx).all()))

arr=jnp.arange(12,dtype=jnp.float32).reshape(3,4)
vm=jax.vmap(lambda v: (v*v).sum())(arr)
print("vmap:", np.array(vm))

nd=jax.local_device_count()
if nd>=2:
    xs=jnp.arange(nd*4.,dtype=jnp.float32).reshape(nd,4)
    @jax.pmap
    def reduce_sum(x): return x.sum()
    rs=reduce_sum(xs)
    print("pmap sums:", np.array(rs))

print("OK: JAX")
