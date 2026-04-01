import os, tempfile
import pandas as pd
import fastparquet
import fastparquet.cencoding
import fastparquet.speedups
from fastparquet import ParquetFile

df = pd.DataFrame({
    'a': [1, 2, 3],
    'b': ['x', 'y', 'z'],
})

with tempfile.TemporaryDirectory() as td:
    fn = os.path.join(td, 'test.parquet')
    df.to_parquet(fn, engine='fastparquet')
    out = pd.read_parquet(fn, engine='fastparquet')
    assert out.equals(df)

    pf = ParquetFile(fn)
    out2 = pf.to_pandas()
    assert out2.equals(df)

print('fastparquet version:', fastparquet.__version__)
print('fastparquet import + extensions + roundtrip OK')