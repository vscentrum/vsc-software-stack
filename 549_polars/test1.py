import polars as pl
import numpy as np

# Generate a large synthetic dataset
# Adjust the size based on your system's memory to ensure streaming is engaged
data_size = 1_000_000
n_groups = 1000

df_lazy = pl.LazyFrame({
    "group_key": np.random.randint(0, n_groups, data_size),
    "value": np.random.rand(data_size),
    "category": np.random.choice(['A', 'B', 'C', 'D'], data_size),
})

print("--- Streaming Group By Test ---")

try:
    # Perform a group by and aggregation in streaming mode
    streaming_result = df_lazy.group_by("group_key").agg([
        pl.col("value").mean().alias("mean_value"),
        pl.col("category").n_unique().alias("n_unique_categories")
    ]).sort("group_key").collect(engine='streaming') # Use streaming engine

    print("\nStreaming Group By Result (first 5 rows):")
    print(streaming_result.head())

    # Optional: Compare with non-streaming result for correctness
    # Be cautious with memory if the dataset is very large
    try:
        non_streaming_result = df_lazy.group_by("group_key").agg([
            pl.col("value").mean().alias("mean_value"),
            pl.col("category").n_unique().alias("n_unique_categories")
        ]).sort("group_key").collect()

        print("\nNon-Streaming Group By Result (first 5 rows):")
        print(non_streaming_result.head())

        # Assert that the results are equal
        assert streaming_result.equals(non_streaming_result), "Streaming and non-streaming results do not match!"
        print("\nStreaming and non-streaming Group By results match.")

    except Exception as e:
        print(f"\nCould not perform non-streaming comparison due to: {e}")


except Exception as e:
    print(f"\nError during streaming group by: {e}")

print("\n--- End of Streaming Group By Test ---")