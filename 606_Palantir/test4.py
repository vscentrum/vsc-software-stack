# -*- coding: utf-8 -*-
import sys, json, importlib, platform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

mods = ["palantir","matplotlib","ml_dtypes","igraph","scanpy","anndata","numpy","pandas","scipy","sklearn","jax","jaxopt"]
info = {"python": sys.version.split()[0], "platform": platform.platform(), "versions": {}, "checks": {}}
errors = {}

for m in mods:
    try:
        mod = importlib.import_module(m)
        info["versions"][m] = getattr(mod, "__version__", getattr(mod, "version", "unknown"))
    except Exception as e:
        errors[m] = repr(e)

# minimal matplotlib smoke: create and save a tiny figure
try:
    plt.figure(); plt.plot([0,1],[0,1]); plt.title("matplotlib smoke"); plt.savefig("matplotlib_smoke.png")
    info["checks"]["matplotlib_savefig"] = True
except Exception as e:
    info["checks"]["matplotlib_savefig"] = False
    errors["matplotlib_savefig"] = repr(e)

# igraph import + tiny graph op
try:
    import igraph as ig
    g = ig.Graph.Erdos_Renyi(10, 0.2)
    _ = g.clusters()
    info["checks"]["igraph_basic"] = True
except Exception as e:
    info["checks"]["igraph_basic"] = False
    errors["igraph_basic"] = repr(e)

# scanpy minimal import smoke
try:
    import scanpy as sc
    info["checks"]["scanpy_import"] = True
except Exception as e:
    info["checks"]["scanpy_import"] = False
    errors["scanpy_import"] = repr(e)

print(json.dumps({"env": info, "errors": errors}, indent=2))
