
import sys, json
import numpy as np
import jax, jax.numpy as jnp

def _get_dist_ver(name):
    try:
        import importlib.metadata as im
        return im.version(name)
    except Exception:
        return None

RES={"checks":[], "errors":[], "skipped":[], "versions":{}, "env":{}}

try:
    import triton, triton.language as tl
    RES["checks"].append("triton_import_ok")
    RES["versions"]["triton"] = getattr(triton, "__version__", None) or _get_dist_ver("triton")
except Exception as e:
    RES["errors"].append("triton_import_failed: "+repr(e))
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(1)

try:
    import jax_triton as jt
    RES["checks"].append("jax_triton_import_ok")
    RES["versions"]["jax_triton_mod"] = getattr(jt, "__version__", None)
    RES["versions"]["jax_triton_pkg"] = _get_dist_ver("jax-triton")
except Exception as e:
    RES["errors"].append("jax_triton_import_failed: "+repr(e))
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(1)

RES["versions"]["python"] = sys.version.split()[0]
RES["versions"]["jax"] = getattr(jax, "__version__", None)

if RES["versions"]["jax"] and not RES["versions"]["jax"].startswith("0.6.2"):
    RES["errors"].append(f"expected JAX 0.6.2; found {RES['versions']['jax']}")
else:
    RES["checks"].append("jax_version_ok")

if RES["versions"]["jax_triton_pkg"] and RES["versions"]["jax_triton_pkg"] != "0.3.0":
    RES["errors"].append(f"expected jax-triton 0.3.0; found {RES['versions']['jax_triton_pkg']}")
else:
    RES["checks"].append("jax_triton_version_ok")

gpus = jax.devices("gpu")
if not gpus:
    RES["skipped"] += ["no_gpu_device_found", "kernel_runs"]
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(0)
dev = gpus[0]
RES["env"]["gpu"]={"platform":dev.platform,"device_kind":dev.device_kind,"id":getattr(dev,"id",None)}

def _cdiv(a,b):
    try: return triton.cdiv(a,b)
    except Exception: return (a + b - 1)//b

@triton.jit
def add_out_last(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)

def grid_1d(n): return lambda meta: (_cdiv(n, meta["BLOCK_SIZE"]),)

def add_triton(a, b):
    n=a.size
    out_shape=jax.ShapeDtypeStruct(a.shape, a.dtype)
    return jt.triton_call(a, b, kernel=add_out_last, out_shape=out_shape, grid=grid_1d(n), n_elements=n, BLOCK_SIZE=256)

# -- eager
try:
    n=4096+123
    x=jax.device_put(jnp.arange(n,dtype=jnp.float32),dev)
    y=jax.device_put(jnp.ones(n,dtype=jnp.float32),dev)
    o=add_triton(x,y); _=np.array(o)
    if not np.allclose(np.array(o), np.array(x+y)): raise AssertionError("eager mismatch")
    RES["checks"].append("triton_eager_add_ok")
except Exception as e:
    RES["errors"].append("triton_eager_add_failed: "+repr(e))

# -- jit
try:
    jf=jax.jit(add_triton)
    z=jf(x,y).block_until_ready()
    if not np.allclose(np.array(z), np.array(x+y)): raise AssertionError("jit mismatch")
    RES["checks"].append("triton_jit_add_ok")
except Exception as e:
    RES["errors"].append("triton_jit_add_failed: "+repr(e))

# -- manual batching without vmap: flatten (B,N) to (B*N)
try:
    B=4; N=n
    xb=jax.device_put(jnp.arange(B*N,dtype=jnp.float32).reshape(B,N),dev)
    yb=jax.device_put(jnp.ones((B,N),dtype=jnp.float32),dev)
    xb_f=xb.reshape(-1); yb_f=yb.reshape(-1)
    out_f=jax.jit(add_triton)(xb_f,yb_f).block_until_ready()
    out=out_f.reshape(B,N)
    if tuple(out.shape)!=(B,N) or not np.allclose(np.array(out), np.array(xb+yb)):
        raise AssertionError("manual_batch_mismatch")
    RES["checks"].append("manual_batch_flatten_ok")
except Exception as e:
    RES["errors"].append("manual_batch_flatten_failed: "+repr(e))

# -- gradient: expect failure or no support; just probe that calling grad raises NotImplementedError cleanly
try:
    g=jax.grad(lambda t: jnp.sum(add_triton(t, jnp.ones_like(t))))(x)
    RES["skipped"].append("grad_supported")
except Exception as e:
    RES["checks"].append("grad_not_supported_expected")

print(json.dumps(RES, indent=2, sort_keys=True))
sys.exit(0 if len(RES["errors"])==0 else 1)
