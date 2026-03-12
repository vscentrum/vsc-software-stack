import os, sys, traceback
import pandas as pd

def main():
    import dask
    import distributed
    import dask_expr
    import dask.dataframe as dd
    from dask.distributed import Client, LocalCluster

    print("dask:", dask.__version__, dask.__file__)
    print("distributed:", distributed.__version__, distributed.__file__)
    print("dask_expr:", dask_expr.__version__, dask_expr.__file__)

    cluster = LocalCluster(n_workers=2, threads_per_worker=1, processes=True)
    client = Client(cluster)

    try:
        pdf1 = pd.DataFrame({
            "k": [0,1,2,3,4,5,6,7,8,9] * 100,
            "x": list(range(1000)),
        })
        pdf2 = pd.DataFrame({
            "k": list(range(10)),
            "y": [v * 10 for v in range(10)],
        })

        ddf1 = dd.from_pandas(pdf1, npartitions=4)
        ddf2 = dd.from_pandas(pdf2, npartitions=2)

        merged = ddf1.merge(ddf2, on="k", how="left")
        grouped = merged.groupby("k")[["x", "y"]].sum()
        shuffled = merged.shuffle("k")
        indexed = shuffled.set_index("k").persist()

        out1 = grouped.compute().sort_index()
        out2 = indexed.head(10)

        print("groupby result:")
        print(out1.head())
        print("indexed head:")
        print(out2)

        fut = client.submit(lambda: sum(range(10)))
        print("distributed task result:", fut.result())

        print("CPU Dask stack OK")
    finally:
        client.close()
        cluster.close()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise