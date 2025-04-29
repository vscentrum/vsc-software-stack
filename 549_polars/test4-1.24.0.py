# streaming_join_test.py

import warnings
import polars as pl
import polars.testing as pt
import numpy as np

# silence the deprecation warning about the old streaming engine
warnings.filterwarnings(
    "ignore",
    message="The old streaming engine is being deprecated and will soon be replaced*"
)

def main():
    # reproducible random data
    np.random.seed(42)
    data_size, n_keys = 500_000, 5_000

    left = (
        pl.DataFrame({
            "join_key": np.random.randint(0, n_keys, data_size),
            "left_value": np.random.rand(data_size),
        })
        .lazy()
    )
    right = (
        pl.DataFrame({
            "join_key": np.random.randint(0, n_keys, data_size),
            "right_value": np.random.rand(data_size),
        })
        .lazy()
    )

    # ---- Inner Join ----
    print("=== Streaming Join Test: INNER ===\n")

    plan_inner = left.join(right, on="join_key", how="inner").explain(streaming=True)
    print(">> Streaming Inner Join Plan:")
    print(plan_inner)
    print("-" * 60)

    streaming_inner = (
        left.join(right, on="join_key", how="inner")
            .sort("join_key")
            .collect(streaming=True)
    )
    print("\nStreaming Inner Join (first 5 rows):")
    print(streaming_inner.head())

    eager_inner = (
        left.join(right, on="join_key", how="inner")
            .sort("join_key")
            .collect()
    )
    print("\nEager Inner Join (first 5 rows):")
    print(eager_inner.head())

    try:
        pt.assert_frame_equal(streaming_inner, eager_inner,
                              check_row_order=True,
                              check_column_order=True)
        print("\n✅ INNER join results match.\n")
    except AssertionError as err:
        print("\n❌ INNER join mismatch:\n", err)
        raise

    # ---- Left Join ----
    print("=== Streaming Join Test: LEFT ===\n")

    plan_left = left.join(right, on="join_key", how="left").explain(streaming=True)
    print(">> Streaming Left Join Plan:")
    print(plan_left)
    print("-" * 60)

    streaming_left = (
        left.join(right, on="join_key", how="left")
            .sort("join_key")
            .collect(streaming=True)
    )
    print("\nStreaming Left Join (first 5 rows):")
    print(streaming_left.head())

    eager_left = (
        left.join(right, on="join_key", how="left")
            .sort("join_key")
            .collect()
    )
    print("\nEager Left Join (first 5 rows):")
    print(eager_left.head())

    try:
        pt.assert_frame_equal(streaming_left, eager_left,
                              check_row_order=True,
                              check_column_order=True)
        print("\n✅ LEFT join results match.")
    except AssertionError as err:
        print("\n❌ LEFT join mismatch:\n", err)
        raise

if __name__ == "__main__":
    main()
