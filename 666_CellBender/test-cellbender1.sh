#!/bin/bash

set -euo pipefail

EXPECTED_VERSION="${EXPECTED_VERSION:-0.4.0}"
export MPLBACKEND=Agg

workdir=$(mktemp -d "${TMPDIR:-/tmp}/cellbender-smoke.XXXXXX")
trap 'rm -rf "$workdir"' EXIT

echo "=== CellBender smoke test ==="
echo "Python:     $(command -v python)"
echo "CellBender: $(command -v cellbender)"
echo "Workdir:    $workdir"
echo

echo "=== 1. CLI ==="

cellbender --help >/dev/null
cellbender remove-background --help >/dev/null

echo "PASS: CLI commands"

echo
echo "=== 2. Python dependencies and version ==="

EXPECTED_VERSION="$EXPECTED_VERSION" python -s <<'PY'
import importlib
import importlib.metadata
import os

packages = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("tables", "tables"),
    ("pandas", "pandas"),
    ("pyro", "pyro-ppl"),
    ("torch", "torch"),
    ("matplotlib", "matplotlib"),
    ("anndata", "anndata"),
    ("IPython", "ipython"),
    ("ipykernel", "ipykernel"),
    ("nbconvert", "nbconvert"),
    ("jupyter_server", "jupyter-server"),
    ("lxml.etree", "lxml"),
    ("lxml_html_clean", "lxml-html-clean"),
    ("psutil", "psutil"),
    ("dill", "dill"),
]

for module, distribution in packages:
    importlib.import_module(module)
    version = importlib.metadata.version(distribution)
    print(f"{distribution:20s} {version}")

import cellbender

expected = os.environ["EXPECTED_VERSION"]
installed = importlib.metadata.version("cellbender")

assert installed == expected, f"CellBender distribution version is {installed}, expected {expected}"
assert cellbender.__version__ == expected, (
    f"cellbender.__version__ is {cellbender.__version__}, expected {expected}"
)

print(f"cellbender           {installed}")
print("PASS: Python imports and CellBender version")
PY

echo
echo "=== 3. PyTorch CPU/CUDA ==="

python -s <<'PY'
import torch

x = torch.arange(16, dtype=torch.float32).reshape(4, 4)
y = x @ x.T

assert y.shape == (4, 4)
assert torch.isfinite(y).all()

print(f"PyTorch:       {torch.__version__}")
print(f"CUDA runtime:  {torch.version.cuda}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    device = torch.cuda.get_device_name(0)
    x = torch.randn(512, 512, device="cuda")
    y = x @ x.T
    torch.cuda.synchronize()

    assert y.is_cuda
    assert torch.isfinite(y).all()

    print(f"CUDA device:   {device}")
    print("PASS: CUDA tensor computation")
else:
    print("SKIP: no CUDA device visible")

print("PASS: PyTorch CPU computation")
PY

if [[ "${CELLBENDER_REQUIRE_CUDA:-0}" == "1" ]]; then
    if ! python -s -c 'import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)'; then
        echo "FAIL: CELLBENDER_REQUIRE_CUDA=1 but no CUDA device is available" >&2
        exit 1
    fi
fi

echo
echo "=== 4. Generate synthetic scRNA-seq input ==="

python -s - "$workdir/input.h5ad" <<'PY'
import sys

import anndata
import numpy as np
import scipy.sparse as sp

output = sys.argv[1]

rng = np.random.default_rng(12345)

n_droplets = 2000
n_cells = 100
n_genes = 200

ambient = rng.dirichlet(np.full(n_genes, 0.3))
cell_profiles = [
    rng.dirichlet(np.full(n_genes, 0.15)),
    rng.dirichlet(np.full(n_genes, 0.15)),
]

counts = np.zeros((n_droplets, n_genes), dtype=np.int32)

for i in range(n_droplets):
    ambient_umi = rng.poisson(200)
    counts[i] += rng.multinomial(ambient_umi, ambient)

    if i < n_cells:
        cell_umi = rng.poisson(4000)
        profile = cell_profiles[0 if i < n_cells // 2 else 1]
        counts[i] += rng.multinomial(cell_umi, profile)

adata = anndata.AnnData(X=sp.csr_matrix(counts))
adata.obs_names = [f"barcode_{i:06d}" for i in range(n_droplets)]
adata.var_names = [f"gene_{i:04d}" for i in range(n_genes)]

adata.write_h5ad(output)

assert adata.shape == (n_droplets, n_genes)
assert adata.X.nnz > 0

print(f"Created {output}")
print(f"Shape: {adata.shape}")
print(f"Total UMIs: {int(adata.X.sum())}")
print("PASS: synthetic input generation")
PY

run_cellbender()
{
    label="$1"
    shift

    rundir="$workdir/$label"
    mkdir -p "$rundir"

    echo
    echo "=== 5. Full CellBender run: $label ==="

    (
        cd "$rundir"

        cellbender remove-background \
            --input "$workdir/input.h5ad" \
            --output output.h5 \
            --expected-cells 100 \
            --total-droplets-included 1000 \
            --epochs 5 \
            "$@"
    )

    echo
    echo "=== 6. Validate output: $label ==="

    EXPECTED_VERSION="$EXPECTED_VERSION" python -s - "$rundir/output.h5" <<'PY'
import os
import sys
from pathlib import Path

import numpy as np

from cellbender.remove_background import consts
from cellbender.remove_background.downstream import anndata_from_h5

output = Path(sys.argv[1])

assert output.is_file() and output.stat().st_size > 0, f"Missing output: {output}"

prefix = str(output)[:-3]

required = [
    Path(prefix + ".log"),
    Path(prefix + "_cell_barcodes.csv"),
    Path(prefix + "_report.html"),
]

for path in required:
    assert path.is_file() and path.stat().st_size > 0, f"Missing output file: {path}"

adata = anndata_from_h5(str(output), analyzed_barcodes_only=True)

assert adata.n_obs > 0
assert adata.n_vars > 0
assert adata.X.nnz > 0
assert np.all(adata.X.data >= 0), "Negative entries found in output count matrix"

p = np.asarray(adata.obs["cell_probability"])

assert np.all(np.isfinite(p)), "Non-finite cell probabilities"
assert np.all((p >= 0.0) & (p <= 1.0)), "Cell probabilities outside [0, 1]"

csv_file = Path(prefix + "_cell_barcodes.csv")
csv_barcodes = {
    line.strip()
    for line in csv_file.read_text().splitlines()
    if line.strip()
}

adata_barcodes = set(
    adata.obs_names[adata.obs["cell_probability"] > consts.CELL_PROB_CUTOFF]
)

assert csv_barcodes == adata_barcodes, (
    "Cell calls in output HDF5 and _cell_barcodes.csv differ"
)

print(f"Output shape:       {adata.shape}")
print(f"Output nonzeros:    {adata.X.nnz}")
print(f"Called cells:       {len(csv_barcodes)}")
print(f"Probability range:  {p.min():.6f} .. {p.max():.6f}")
print("PASS: CellBender output validation")
PY

    grep -F "CellBender $EXPECTED_VERSION" "$rundir/output.log" >/dev/null

    echo "PASS: CellBender $label full run"
}

run_cellbender cpu

if python -s -c 'import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)'; then
    run_cellbender cuda --cuda
else
    echo
    echo "SKIP: full CUDA CellBender run because no GPU is visible"
fi

echo
echo "========================================"
echo "ALL CELLBENDER SMOKE TESTS PASSED"
echo "========================================"