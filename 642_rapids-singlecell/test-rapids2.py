import os
import traceback

def main():
    import dask
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster
    import cudf
    import dask_cudf

    print("dask:", dask.__version__, dask.__file__)

    cluster = LocalCUDACluster(
        CUDA_VISIBLE_DEVICES="0",
        protocol="tcp",
        n_workers=1,
        threads_per_worker=1,
    )
    client = Client(cluster)

    try:
        df = cudf.DataFrame({
            "src": [0, 1, 2, 2, 3, 3],
            "dst": [1, 2, 0, 3, 4, 5],
            "w":   [1, 1, 1, 1, 1, 1],
        })
        ddf = dask_cudf.from_cudf(df, npartitions=2)
        out = ddf.groupby("src").w.sum().compute()
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