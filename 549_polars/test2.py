import polars as pl
import numpy as np

# Generate two large synthetic datasets for joining
data_size_left = 500_000
data_size_right = 500_000
n_join_keys = 5000

left_df_lazy = pl.LazyFrame({
    "join_key": np.random.randint(0, n_join_keys, data_size_left),
    "left_value": np.random.rand(data_size_left),
})

right_df_lazy = pl.LazyFrame({
    "join_key": np.random.randint(0, n_join_keys, data_size_right),
    "right_value": np.random.rand(data_size_right),
})

print("\n--- Streaming Join Test (Inner Join) ---")

try:
    # Perform a streaming inner join
    streaming_join_result_inner = left_df_lazy.join(
        right_df_lazy, on="join_key", how="inner"
    ).sort("join_key").collect(engine='streaming')

    print("\nStreaming Inner Join Result (first 5 rows):")
    print(streaming_join_result_inner.head())

    # Optional: Compare with non-streaming inner join
    try:
        non_streaming_join_result_inner = left_df_lazy.join(
            right_df_lazy, on="join_key", how="inner"
        ).sort("join_key").collect()

        print("\nNon-Streaming Inner Join Result (first 5 rows):")
        print(non_streaming_join_result_inner.head())

        # Assert that the results are equal
        assert streaming_join_result_inner.equals(non_streaming_join_result_inner), "Streaming and non-streaming inner join results do not match!"
        print("\nStreaming and non-streaming Inner Join results match.")

    except Exception as e:
        print(f"\nCould not perform non-streaming inner join comparison due to: {e}")

except Exception as e:
    print(f"\nError during streaming inner join: {e}")

print("\n--- End of Streaming Join Test (Inner Join) ---")

print("\n--- Streaming Join Test (Left Join) ---")

try:
    # Perform a streaming left join
    streaming_join_result_left = left_df_lazy.join(
        right_df_lazy, on="join_key", how="left"
    ).sort("join_key").collect(engine='streaming')

    print("\nStreaming Left Join Result (first 5 rows):")
    print(streaming_join_result_left.head())

    # Optional: Compare with non-streaming left join
    try:
        non_streaming_join_result_left = left_df_lazy.join(
            right_df_lazy, on="join_key", how="left"
        ).sort("join_key").collect()

        print("\nNon-Streaming Left Join Result (first 5 rows):")
        print(non_streaming_join_result_left.head())

        # Assert that the results are equal
        assert streaming_join_result_left.equals(non_streaming_join_result_left), "Streaming and non-streaming left join results do not match!"
        print("\nStreaming and non-streaming Left Join results match.")

    except Exception as e:
        print(f"\nCould not perform non-streaming left join comparison due to: {e}")

except Exception as e:
    print(f"\nError during streaming left join: {e}")

print("\n--- End of Streaming Join Test (Left Join) ---")

# You can add more join types (e.g., 'outer', 'semi', 'anti') to test further