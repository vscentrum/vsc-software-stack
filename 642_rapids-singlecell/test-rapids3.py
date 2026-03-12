import os, sys, time, traceback, platform, importlib.metadata as md
from packaging.requirements import Requirement

def section(name):
    print(f"\n========== {name} ==========")

def pkgver(name):
    try:
        return md.version(name)
    except Exception:
        return "not-installed"

def run_check(name, fn):
    section(name)
    t0 = time.time()
    try:
        fn()
        print(f"OK ({time.time() - t0:.2f}s)")
        return True
    except Exception:
        print(f"FAIL ({time.time() - t0:.2f}s)")
        traceback.print_exc()
        return False

def active_requirements(dist_name, wanted):
    reqs = []
    for raw in md.requires(dist_name) or []:
        req = Requirement(raw)
        if req.marker and not req.marker.evaluate():
            continue
        if req.name.lower() in wanted:
            reqs.append(req)
    return reqs

def check_requirements(owner, reqs):
    for req in reqs:
        inst = pkgver(req.name)
        ok = inst != "not-installed" and req.specifier.contains(inst, prereleases=True)
        print(f"{owner}: {req.name} {req.specifier} ; installed={inst} ; ok={ok}")
        if not ok:
            raise RuntimeError(f"{owner} requires {req.name}{req.specifier}, installed {inst}")

print("python:", sys.version.split()[0])
print("platform:", platform.platform())
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>"))
print("NUMBA_CUDA_USE_NVIDIA_BINDING:", os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING", "<unset>"))
print("LD_LIBRARY_PATH:", os.environ.get("LD_LIBRARY_PATH", "<unset>"))
print()

print("package versions:")
for name in [
    "cuda-python",
    "cupy-cuda12x",
    "cudf-cu12",
    "cuml-cu12",
    "cugraph-cu12",
    "rmm-cu12",
    "dask",
    "distributed",
    "dask-expr",
    "dask-cuda",
    "dask-cudf-cu12",
    "rapids-dask-dependency",
    "ucx-py-cu12",
    "ucxx-cu12",
]:
    print(f"  {name}: {pkgver(name)}")

results = []

def check_env():
    val = os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING")
    if val != "1":
        raise RuntimeError("NUMBA_CUDA_USE_NVIDIA_BINDING must be 1")
    print("NUMBA_CUDA_USE_NVIDIA_BINDING=1")

results.append(run_check("Required env", check_env))

def check_dask_requirements():
    reqs = active_requirements("rapids-dask-dependency", {"dask", "distributed"})
    check_requirements("rapids-dask-dependency", reqs)
    reqs = active_requirements("dask-expr", {"dask"})
    check_requirements("dask-expr", reqs)

results.append(run_check("Dask metadata compatibility", check_dask_requirements))

def check_dask_stack():
    import dask, distributed, dask_expr
    import pandas as pd
    import dask.dataframe as dd

    print("dask:", dask.__version__, dask.__file__)
    print("distributed:", distributed.__version__, distributed.__file__)
    print("dask_expr:", dask_expr.__version__, dask_expr.__file__)

    pdf = pd.DataFrame({"a": [1, 2, 1, 3], "b": [10, 20, 30, 40]})
    ddf = dd.from_pandas(pdf, npartitions=2)
    out = ddf.groupby("a").b.sum().compute().sort_index()
    print(out)

results.append(run_check("Dask stack import", check_dask_stack))

def check_cuda_python():
    from cuda import cuda as cu
    (err,) = cu.cuInit(0)
    print("cuInit:", err)
    err, ndev = cu.cuDeviceGetCount()
    print("device_count:", ndev)
    if ndev < 1:
        raise RuntimeError("No CUDA devices found")

results.append(run_check("CUDA-Python low-level", check_cuda_python))

def check_cupy():
    import cupy as cp
    x = cp.arange(10, dtype=cp.float32)
    y = cp.sin(x).sum()
    cp.cuda.runtime.deviceSynchronize()
    props = cp.cuda.runtime.getDeviceProperties(0)
    print("cupy:", cp.__version__)
    print("gpu:", props["name"].decode())
    print("sum(sin(arange(10))):", float(y))

results.append(run_check("CuPy basic", check_cupy))

def check_cudf():
    import cudf, cupy as cp
    df = cudf.DataFrame({
        "a": cp.arange(1000, dtype=cp.int32),
        "b": cp.random.randint(0, 10, size=1000, dtype=cp.int32),
        "x": cp.random.random(1000, dtype=cp.float32),
    })
    out = df.groupby("b").agg({"x": "mean"}).sort_index()
    print("cudf:", cudf.__version__)
    print("groupby rows:", len(out))
    print("to_numpy head:", out["x"].to_numpy()[:5])
    print(out.head().to_pandas())

results.append(run_check("cuDF basic", check_cudf))

def check_cuml():
    import cupy as cp
    from cuml.cluster import KMeans
    X = cp.asarray([[0.0,0.0],[0.1,0.1],[9.0,9.0],[9.1,9.2]], dtype=cp.float32)
    km = KMeans(n_clusters=2, random_state=0, n_init=1, max_iter=20)
    labels = km.fit_predict(X)
    cp.cuda.runtime.deviceSynchronize()
    print("labels:", labels.get().tolist())
    print("cluster_centers:", km.cluster_centers_.get().tolist())

results.append(run_check("cuML basic", check_cuml))

def check_cugraph():
    import cudf, cugraph
    gdf = cudf.DataFrame({"src": [0,1,2,2], "dst": [1,2,0,3]})
    G = cugraph.Graph(directed=True)
    G.from_cudf_edgelist(gdf, source="src", destination="dst", store_transposed=True)
    pr = cugraph.pagerank(G).sort_values("pagerank", ascending=False)
    print("cugraph:", cugraph.__version__)
    print(pr.head().to_pandas())

results.append(run_check("cuGraph basic", check_cugraph))

def check_ucx_imports():
    import ucp, ucxx
    print("ucp import OK:", ucp.__file__)
    print("ucxx import OK:", ucxx.__file__)

results.append(run_check("UCX Python imports", check_ucx_imports))

print("\n========== SUMMARY ==========")
passed = sum(bool(x) for x in results)
total = len(results)
print(f"passed {passed}/{total} checks")
if passed != total:
    sys.exit(1)