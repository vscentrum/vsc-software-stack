
import os, sys, time, shutil
# Optional persistent cache
cache_dir = os.environ.get("JAX_PERSISTENT_CACHE") or os.environ.get("JAX_COMPILATION_CACHE_DIR") or None
if cache_dir:
    try:
        from jax.experimental.compilation_cache import compilation_cache as cc
        cc.set_cache_dir(cache_dir)
    except Exception:
        try:
            from jax._src.compilation_cache import set_cache_dir as _set_cache_dir
            _set_cache_dir(cache_dir)
        except Exception:
            pass

import jax, jax.numpy as jnp

def bench(shape=(1024,1024), dtype=jnp.float16, iters=5, warmups=1):
    key = jax.random.key(0)
    a = jax.random.normal(key, shape, dtype=dtype)
    b = jax.random.normal(key, shape, dtype=dtype)

    @jax.jit
    def mm(x,y): return x @ y

    # compile + first run
    t0=time.time(); out = mm(a,b).block_until_ready(); t1=time.time()
    # ensure finite reduction (upcast for sum)
    s = float(jnp.sum(out.astype(jnp.float32)))
    runs=[]
    for _ in range(iters):
        t2=time.time(); out = mm(a,b).block_until_ready(); t3=time.time()
        runs.append((t3-t2)*1000.0)
    return {"shape": shape, "dtype": str(dtype), "compile_plus_run_ms": int((t1-t0)*1000.0),
            "steady_ms_mean": round(sum(runs)/len(runs),1), "steady_ms_min": round(min(runs),1),
            "sum32": s, "backend": jax.default_backend(), "devices": [str(d) for d in jax.devices()]}

if __name__ == "__main__":
    res = bench()
    print("backend:", res["backend"])
    print("devices:", ", ".join(res["devices"]))
    print("shape:", res["shape"], "dtype:", res["dtype"])
    print("compile_plus_run_ms:", res["compile_plus_run_ms"])
    print("steady_ms_mean:", res["steady_ms_mean"])
    print("steady_ms_min:", res["steady_ms_min"])
    print("sum32:", res["sum32"])
