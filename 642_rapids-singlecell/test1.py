import os, sys, time, traceback, importlib.util as u

def have(mod): return u.find_spec(mod) is not None
def banner(s): print("\n" + "="*10 + f" {s} " + "="*10, flush=True)

def try_run(name, fn):
    banner(name)
    t0=time.time()
    try:
        out=fn()
        dt=time.time()-t0
        print(f"OK ({dt:.2f}s)")
        if out is not None: print(out)
        return True
    except Exception as e:
        dt=time.time()-t0
        print(f"FAIL ({dt:.2f}s): {e}")
        traceback.print_exc()
        return False

def env_info():
    import platform
    import numpy as np
    print("python:", sys.version.split()[0])
    print("platform:", platform.platform())
    print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>"))
    print("numpy:", np.__version__)

def cuda_driver():
    import ctypes
    ctypes.CDLL("libcuda.so.1")
    return "libcuda.so.1 loaded"

def cupy_basic():
    import cupy as cp
    a=cp.arange(10, dtype=cp.float32)
    b=cp.sin(a).sum()
    cp.cuda.runtime.deviceSynchronize()
    free,total=cp.cuda.runtime.memGetInfo()
    return f"cupy {cp.__version__} ok; sin-sum={float(b):.6f}; mem_free={free/1e9:.2f}GB"

def cudf_basic():
    import cudf
    import cupy as cp
    df=cudf.DataFrame({"a":[1,2,3], "b":[10,20,30]})
    df["c"]=df["a"]+df["b"]
    s=int(df["c"].sum())
    # small gpu roundtrip check
    g=cp.asarray(df["c"].to_numpy())
    cp.cuda.runtime.deviceSynchronize()
    return f"cudf {cudf.__version__} ok; sum(c)={s}; cupy_arr_sum={int(g.sum())}"

def cuml_basic():
    import cupy as cp
    from cuml.linear_model import LogisticRegression
    X=cp.asarray([[0,0],[1,1],[1,0],[0,1]], dtype=cp.float32)
    y=cp.asarray([0,1,1,0], dtype=cp.int32)
    m=LogisticRegression(max_iter=200)
    m.fit(X,y)
    p=m.predict(X)
    cp.cuda.runtime.deviceSynchronize()
    return f"cuml ok; pred={cp.asnumpy(p).tolist()}"

def cugraph_basic():
    import cudf
    import cugraph
    edgelist=cudf.DataFrame({"src":[0,1,2,2], "dst":[1,2,0,3], "w":[1.0,1.0,1.0,1.0]})
    G=cugraph.Graph(directed=True)
    G.from_cudf_edgelist(edgelist, source="src", destination="dst", edge_attr="w")
    pr=cugraph.pagerank(G)
    top=pr.sort_values("pagerank", ascending=False).head(3)
    return f"cugraph {cugraph.__version__} ok; top3={top.to_pandas().to_dict('records')}"

def rapids_singlecell_basic():
    import rapids_singlecell as rsc
    info=f"rapids_singlecell {getattr(rsc,'__version__','<unknown>')} imported"
    # Try a small neighbors call if API exists (varies across versions)
    if have("anndata") and have("cupy"):
        import numpy as np
        import anndata as ad
        import cupy as cp
        X=cp.asarray(np.random.RandomState(0).randn(50, 10).astype("float32"))
        a=ad.AnnData(X=cp.asnumpy(X))  # keep AnnData CPU-backed for compatibility
        if hasattr(rsc, "pp") and hasattr(rsc.pp, "neighbors"):
            rsc.pp.neighbors(a, n_neighbors=10, use_rep="X")
            info += "; neighbors() ok"
    return info

def dask_cuda_basic():
    from dask_cuda import LocalCUDACluster
    from dask.distributed import Client
    import cupy as cp
    cluster=LocalCUDACluster()
    client=Client(cluster)
    try:
        x=cp.arange(1_000_000, dtype=cp.float32)
        # run a small GPU task on workers
        fut=client.submit(lambda arr: float(arr.sum()), x)
        res=fut.result(timeout=60)
        return f"dask-cuda ok; sum={res}"
    finally:
        client.close()
        cluster.close()

def main():
    env_info()
    ok=[]
    ok.append(try_run("CUDA driver", cuda_driver))
    if have("cupy"): ok.append(try_run("CuPy basic", cupy_basic))
    else: print("Skipping CuPy: not importable")
    if have("cudf"): ok.append(try_run("cuDF basic", cudf_basic))
    else: print("Skipping cuDF: not importable")
    if have("cuml"): ok.append(try_run("cuML basic", cuml_basic))
    else: print("Skipping cuML: not importable")
    if have("cugraph"): ok.append(try_run("cuGraph basic", cugraph_basic))
    else: print("Skipping cuGraph: not importable")
    if have("rapids_singlecell"): ok.append(try_run("rapids-singlecell basic", rapids_singlecell_basic))
    else: print("Skipping rapids-singlecell: not importable")
    if have("dask_cuda") and have("distributed"):
        ok.append(try_run("Dask-CUDA basic", dask_cuda_basic))
    else:
        print("Skipping Dask-CUDA: dask_cuda/distributed not importable")
    banner("SUMMARY")
    print(f"passed {sum(ok)}/{len(ok)} checks")
    sys.exit(0 if all(ok) else 1)

if __name__=="__main__":
    main()