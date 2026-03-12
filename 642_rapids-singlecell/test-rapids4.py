import os, traceback, importlib.metadata as md
from packaging.requirements import Requirement

def pkgver(name):
    try:
        return md.version(name)
    except Exception:
        return "not-installed"

def active_requirements(dist_name, wanted):
    reqs = []
    for raw in md.requires(dist_name) or []:
        req = Requirement(raw)
        if req.marker and not req.marker.evaluate():
            continue
        if req.name.lower() in wanted:
            reqs.append(req)
    return reqs

def check_requirements():
    for owner, wanted in [
        ("rapids-dask-dependency", {"dask", "distributed"}),
        ("dask-expr", {"dask"}),
    ]:
        for req in active_requirements(owner, wanted):
            inst = pkgver(req.name)
            ok = inst != "not-installed" and req.specifier.contains(inst, prereleases=True)
            print(f"{owner}: {req.name} {req.specifier} ; installed={inst} ; ok={ok}")
            if not ok:
                raise RuntimeError(f"{owner} requires {req.name}{req.specifier}, installed {inst}")

def main():
    if os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING") != "1":
        raise RuntimeError("NUMBA_CUDA_USE_NVIDIA_BINDING must be 1")

    import dask, distributed
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster

    print("dask:", dask.__version__, dask.__file__)
    print("distributed:", distributed.__version__, distributed.__file__)
    print("NUMBA_CUDA_USE_NVIDIA_BINDING:", os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING"))
    check_requirements()

    cluster = LocalCUDACluster(
        CUDA_VISIBLE_DEVICES=os.environ.get("CUDA_VISIBLE_DEVICES", "0"),
        protocol="tcp",
        n_workers=1,
        threads_per_worker=1,
        memory_limit="3GiB",
        device_memory_limit="2GiB",
        enable_cudf_spill=True,
        local_directory=os.environ.get("TMPDIR", "/tmp"),
    )
    client = Client(cluster)

    try:
        import cudf, dask_cudf

        df = cudf.DataFrame({
            "src": [0, 1, 2, 2, 3, 3],
            "dst": [1, 2, 0, 3, 4, 5],
            "w":   [1, 1, 1, 1, 1, 1],
        })
        ddf = dask_cudf.from_cudf(df, npartitions=2)
        out = ddf.groupby("src").w.sum().compute().sort_index()
        print(out.to_pandas())
        print("Dask-CUDA + dask_cudf OK")
    finally:
        client.close()
        cluster.close()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise