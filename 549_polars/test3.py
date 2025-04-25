import polars as pl
import numpy as np

# Generate two synthetic datasets for joining
# You can adjust the size based on your available memory and testing needs
data_size_left = 500_000
data_size_right = 500_000
n_join_keys = 5000 # Number of unique keys

left_df_lazy = pl.LazyFrame({
    "join_key": np.random.randint(0, n_join_keys, data_size_left),
    "left_value": np.random.rand(data_size_left),
})

right_df_lazy = pl.LazyFrame({
    "join_key": np.random.randint(0, n_join_keys, data_size_right),
    "right_value": np.random.rand(data_size_right),
})

print("--- Streaming Join Test (Inner Join) ---")

# Explain the streaming plan for Inner Join
print("\n--- Streaming Inner Join Plan ---")
print(left_df_lazy.join(
    right_df_lazy, on="join_key", how="inner"
).explain(engine='streaming'))
print("---------------------------------")

# Perform a streaming inner join
streaming_join_result_inner = left_df_lazy.join(
    right_df_lazy, on="join_key", how="inner"
).sort("join_key").collect(engine='streaming')

print("\nStreaming Inner Join Result (first 5 rows):")
print(streaming_join_result_inner.head())

# Perform a non-streaming inner join for comparison
non_streaming_join_result_inner = left_df_lazy.join(
    right_df_lazy, on="join_key", how="inner"
).sort("join_key").collect()

print("\nNon-Streaming Inner Join Result (first 5 rows):")
print(non_streaming_join_result_inner.head())

# Assert that the results are equal using .equals()
# Removed try...except to see the actual AssertionError
assert streaming_join_result_inner.equals(non_streaming_join_result_inner), "Streaming and non-streaming inner join results do not match!"
print("\nStreaming and non-streaming Inner Join results match.")

print("\n--- End of Streaming Join Test (Inner Join) ---")

print("\n--- Streaming Join Test (Left Join) ---")

# Explain the streaming plan for Left Join
print("\n--- Streaming Left Join Plan ---")
print(left_df_lazy.join(
    right_df_lazy, on="join_key", how="left"
).explain(engine='streaming'))
print("--------------------------------")

# Perform a streaming left join
streaming_join_result_left = left_df_lazy.join(
    right_df_lazy, on="join_key", how="left"
).sort("join_key").collect(engine='streaming')

print("\nStreaming Left Join Result (first 5 rows):")
print(streaming_join_result_left.head())

# Perform a non-streaming left join for comparison
non_streaming_join_result_left = left_df_lazy.join(
    right_df_lazy, on="join_key", how="left"
).sort("join_key").collect()


print("\nNon-Streaming Left Join Result (first 5 rows):")
print(non_streaming_join_result_left.head())

# Assert that the results are equal using .equals()
# Removed try...except to see the actual AssertionError
assert streaming_join_result_left.equals(non_streaming_join_result_left), "Streaming and non-streaming left join results do not match!"
print("\nStreaming and non-streaming Left Join results match.")


print("\n--- End of Streaming Join Test (Left Join) ---")