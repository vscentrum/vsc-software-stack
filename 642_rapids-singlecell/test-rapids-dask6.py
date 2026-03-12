import os, traceback

def main():
    if os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING") != "1":
        raise RuntimeError("NUMBA_CUDA_USE_NVIDIA_BINDING must be 1")

    import dask
    import distributed
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster

    print("dask:", dask.__version__, dask.__file__)
    print("distributed:", distributed.__version__, distributed.__file__)
    print("NUMBA_CUDA_USE_NVIDIA_BINDING:", os.environ.get("NUMBA_CUDA_USE_NVIDIA_BINDING"))

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
        import cupy as cp
        import cudf
        import dask_cudf

        df1 = cudf.DataFrame({
            "k": cp.asarray([0,1,2,3,4,5,6,7,8,9] * 1000, dtype=cp.int32),
            "x": cp.arange(10000, dtype=cp.int32),
        })
        df2 = cudf.DataFrame({
            "k": cp.arange(10, dtype=cp.int32),
            "y": cp.arange(10, dtype=cp.int32) * 10,
        })

        ddf1 = dask_cudf.from_cudf(df1, npartitions=4)
        ddf2 = dask_cudf.from_cudf(df2, npartitions=2)

        merged = ddf1.merge(ddf2, on="k", how="left")
        grouped = merged.groupby("k")[["x", "y"]].sum()
        shuffled = merged.shuffle(on="k")
        persisted = shuffled.persist()
        out1 = grouped.compute().sort_index()
        out2 = persisted.head(10)

        print("groupby result:")
        print(out1.to_pandas().head())
        print("persisted head:")
        print(out2.to_pandas())

        fut = client.submit(lambda: __import__("cupy").arange(1000, dtype=__import__("cupy").int32).sum().item())
        print("worker cupy task result:", fut.result())

        print("GPU Dask stack OK")
    finally:
        client.close()
        cluster.close()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise