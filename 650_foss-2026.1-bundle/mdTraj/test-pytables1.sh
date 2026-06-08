#!/bin/bash
set -euo pipefail

tmpdir="${TMPDIR:-/tmp}/pytables-smoketest-${USER:-user}-$$"
mkdir -p "$tmpdir"
trap 'rm -rf "$tmpdir"' EXIT

echo "== PyTables import/version check =="
python - <<'PY'
import sys
import numpy as np
import tables as tb

print("python:", sys.version.replace("\n", " "))
print("numpy:", np.__version__)
print("tables:", tb.__version__)
print("hdf5:", tb.get_hdf5_version())
print("blosc:", tb.which_lib_version("blosc"))
print("blosc2:", tb.which_lib_version("blosc2"))
print("zlib:", tb.which_lib_version("zlib"))
print("bzip2:", tb.which_lib_version("bzip2"))
print("lzo:", tb.which_lib_version("lzo"))
PY

echo
echo "== Check whether PyTables links to external classic libblosc =="
sofile="$(python - <<'PY'
import pathlib
import tables
print(pathlib.Path(tables.__file__).parent / "utilsextension.abi3.so")
PY
)"
echo "$sofile"
ldd "$sofile" | grep -Ei 'libblosc|libhdf5|libbz2|libz|liblzo' || true

if ldd "$sofile" | grep -q 'libblosc\.so'; then
    echo "ERROR: PyTables is linked against external classic libblosc.so; expected bundled c-blosc for this EC."
    exit 1
fi

echo
echo "== Compression write/read checks =="
python - <<PY
import os
import tempfile
import numpy as np
import tables as tb

tmpdir = "$tmpdir"
size = 300_000
data = np.fromiter(((i, i * i, i / 3.0) for i in range(size)), dtype="i4,i8,f8")

compressors = [
    "zlib",
    "bzip2",
    "blosc",
    "blosc:blosclz",
    "blosc:lz4",
    "blosc:lz4hc",
    "blosc:zlib",
    "blosc:zstd",
    "blosc2",
]

for complib in compressors:
    fname = tempfile.mktemp(prefix=f"pytables-{complib.replace(':', '-')}-", suffix=".h5", dir=tmpdir)
    print(f"testing {complib} -> {fname}", flush=True)

    with tb.open_file(fname, "w") as h5:
        tab = h5.create_table(
            h5.root,
            "table",
            data,
            filters=tb.Filters(complevel=5, complib=complib),
            chunkshape=(size // 3,),
        )
        tab.flush()

    with tb.open_file(fname, "r") as h5:
        tab = h5.root.table
        assert tab.nrows == size
        assert int(tab[12345]["f0"]) == 12345
        assert int(tab[12345]["f1"]) == 12345 * 12345

    print(f"{complib}: OK")

print("all compression checks passed")
PY

echo
echo "== CLI checks =="
for cmd in pt2to3 ptdump ptrepack pttree; do
    command -v "$cmd"
    "$cmd" --help >/dev/null
    echo "$cmd: OK"
done

echo
echo "PyTables smoke test passed"