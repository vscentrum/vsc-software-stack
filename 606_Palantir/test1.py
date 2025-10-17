import sys, importlib, platform, json
mods = ["palantir","scanpy","anndata","numpy","pandas","scipy","sklearn","numba","matplotlib","umap"]
optional = ["fa2","magic"]
out = {"python": sys.version.split()[0], "platform": platform.platform(), "packages": {}}
errors = {}
for name in mods:
    try:
        m = importlib.import_module(name)
        v = getattr(m, "__version__", getattr(m, "version", "unknown"))
        out["packages"][name] = str(v)
    except Exception as e:
        errors[name] = repr(e)
for name in optional:
    try:
        importlib.import_module(name)
        out["packages"][name] = "present"
    except Exception:
        out["packages"][name] = "missing"
try:
    from numba import jit
    @jit(nopython=True)
    def _acc(x):
        s=0.0
        for i in range(x.shape[0]): s+=x[i]
        return s
    import numpy as np
    _ = _acc(np.arange(10.0))
    out["numba_jit_ok"] = True
except Exception as e:
    out["numba_jit_ok"] = False
    errors["numba_jit"] = repr(e)
print(json.dumps({"env": out, "errors": errors}, indent=2))