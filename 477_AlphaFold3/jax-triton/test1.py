
import sys, json, importlib
import numpy as np
import jax, jax.numpy as jnp

def _get_dist_ver(pkg_name):
    try:
        import importlib.metadata as im
        return im.version(pkg_name)
    except Exception:
        return None

RES={"checks":[], "errors":[], "skipped":[], "versions":{}, "env":{}}

# --- Imports & versions ---
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

# --- Version sanity ---
if RES["versions"]["jax"] and not RES["versions"]["jax"].startswith("0.6.2"):
    RES["errors"].append(f"expected JAX 0.6.2; found {RES['versions']['jax']}")
else:
    RES["checks"].append("jax_version_ok")

if RES["versions"]["jax_triton_pkg"] and RES["versions"]["jax_triton_pkg"] != "0.3.0":
    RES["errors"].append(f"expected jax-triton 0.3.0; found {RES['versions']['jax_triton_pkg']}")
else:
    RES["checks"].append("jax_triton_version_ok")

# --- Device check ---
gpus = jax.devices("gpu")
if not gpus:
    RES["skipped"] += ["no_gpu_device_found", "triton_kernel_run"]
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(0)

dev = gpus[0]
RES["env"]["gpu"] = {"platform": dev.platform, "device_kind": dev.device_kind, "id": getattr(dev, "id", None)}
if dev.platform != "gpu":
    RES["skipped"] += ["unexpected_non_gpu_platform", "triton_kernel_run"]
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(0)

# --- Utility ---
def _cdiv(a,b):
    try:
        return triton.cdiv(a,b)
    except Exception:
        return (a + b - 1) // b

# --- Define two simple add kernels (output last vs first) ---
import triton, triton.language as tl

@triton.jit
def add_out_last(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)

@triton.jit
def add_out_first(out_ptr, x_ptr, y_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)

def _grid_fn(n):
    return lambda meta: (_cdiv(n, meta["BLOCK_SIZE"]),)

def try_modes(x, y):
    n = x.size
    out_shape = jax.ShapeDtypeStruct(x.shape, x.dtype)
    grid = _grid_fn(n)
    errs = []

    # Mode A: output pointer is LAST, pass x,y positionally
    try:
        out = jt.triton_call(x, y, kernel=add_out_last, out_shape=out_shape, grid=grid, n_elements=n, BLOCK_SIZE=256)
        if np.allclose(np.array(out), np.array(x+y)): return out, "mode_pos_out_last"
        else: errs.append("mode_pos_out_last_wrong_result")
    except Exception as e:
        errs.append("mode_pos_out_last_failed: "+repr(e))

    # Mode B: output pointer is FIRST, pass x,y positionally
    try:
        out = jt.triton_call(x, y, kernel=add_out_first, out_shape=out_shape, grid=grid, n_elements=n, BLOCK_SIZE=256)
        if np.allclose(np.array(out), np.array(x+y)): return out, "mode_pos_out_first"
        else: errs.append("mode_pos_out_first_wrong_result")
    except Exception as e:
        errs.append("mode_pos_out_first_failed: "+repr(e))

    # Mode C: output pointer LAST, pass y as kw
    try:
        out = jt.triton_call(x, kernel=add_out_last, out_shape=out_shape, grid=grid, y=y, n_elements=n, BLOCK_SIZE=256)
        if np.allclose(np.array(out), np.array(x+y)): return out, "mode_kw_out_last"
        else: errs.append("mode_kw_out_last_wrong_result")
    except Exception as e:
        errs.append("mode_kw_out_last_failed: "+repr(e))

    # Mode D: output pointer FIRST, pass y as kw
    try:
        out = jt.triton_call(x, kernel=add_out_first, out_shape=out_shape, grid=grid, y=y, n_elements=n, BLOCK_SIZE=256)
        if np.allclose(np.array(out), np.array(x+y)): return out, "mode_kw_out_first"
        else: errs.append("mode_kw_out_first_wrong_result")
    except Exception as e:
        errs.append("mode_kw_out_first_failed: "+repr(e))

    raise RuntimeError("; ".join(errs))

# --- Prepare inputs on GPU ---
n = 4096 + 123
x = jax.device_put(jnp.arange(n, dtype=jnp.float32).reshape(-1), device=dev)
y = jax.device_put(jnp.ones(n, dtype=jnp.float32).reshape(-1), device=dev)

# --- Eager run ---
try:
    out, mode = try_modes(x, y)
    _ = np.array(out)  # materialize to host for validation
    RES["checks"].append("triton_eager_add_ok")
    RES["env"]["triton_call_mode"] = mode
except Exception as e:
    RES["errors"].append("triton_eager_add_failed: "+repr(e))
    print(json.dumps(RES, indent=2, sort_keys=True)); sys.exit(1)

# --- JIT run using the discovered call mode ---
def add_impl(mode):
    def f(a,b):
        n=a.size; out_shape=jax.ShapeDtypeStruct(a.shape, a.dtype); grid=_grid_fn(n)
        if mode=="mode_pos_out_last":
            return jt.triton_call(a, b, kernel=add_out_last, out_shape=out_shape, grid=grid, n_elements=n, BLOCK_SIZE=256)
        if mode=="mode_pos_out_first":
            return jt.triton_call(a, b, kernel=add_out_first, out_shape=out_shape, grid=grid, n_elements=n, BLOCK_SIZE=256)
        if mode=="mode_kw_out_last":
            return jt.triton_call(a, kernel=add_out_last, out_shape=out_shape, grid=grid, y=b, n_elements=n, BLOCK_SIZE=256)
        if mode=="mode_kw_out_first":
            return jt.triton_call(a, kernel=add_out_first, out_shape=out_shape, grid=grid, y=b, n_elements=n, BLOCK_SIZE=256)
        raise RuntimeError("unknown mode "+str(mode))
    return f

try:
    jf = jax.jit(add_impl(mode))
    z = jf(x, y).block_until_ready()
    if not np.allclose(np.array(z), np.array(x+y)):
        raise AssertionError("jit result mismatch")
    RES["checks"].append("triton_jit_add_ok")
except Exception as e:
    RES["errors"].append("triton_jit_add_failed: "+repr(e))

# --- vmapped batch test ---
try:
    xb = jnp.arange(4*n, dtype=jnp.float32).reshape(4,n)
    yb = jnp.ones((4,n), dtype=jnp.float32)
    xb = jax.device_put(xb, device=dev); yb = jax.device_put(yb, device=dev)
    vb = jax.vmap(add_impl(mode))(xb, yb).block_until_ready()
    if tuple(vb.shape)!=(4,n):
        raise AssertionError("vmap shape wrong")
    RES["checks"].append("triton_vmap_add_ok")
except Exception as e:
    RES["errors"].append("triton_vmap_add_failed: "+repr(e))

print(json.dumps(RES, indent=2, sort_keys=True))
sys.exit(0 if len(RES["errors"])==0 else 1)
