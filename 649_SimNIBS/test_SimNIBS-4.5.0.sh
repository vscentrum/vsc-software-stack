#!/usr/bin/env bash
set -euo pipefail

echo "== Basic executable checks =="
which python
which simnibs
simnibs --help >/tmp/simnibs_help.txt
head -n 5 /tmp/simnibs_help.txt || true

echo "== Python import checks =="
python - <<'PY'
import sys
print("Python:", sys.version)

import numpy
import scipy
print("NumPy:", numpy.__version__)
print("SciPy:", scipy.__version__)

from petsc4py import PETSc
print("PETSc:", PETSc.Sys.getVersion())

import simnibs
print("SimNIBS:", getattr(simnibs, "__version__", "unknown"))

from simnibs.mesh_tools import cgal
print("CGAL extension import: OK")

import mumps
import fmm3dpy
import pygpc
import samseg
import surfa
import xxhash
print("Extra dependency imports: OK")
PY

echo "== Runtime linker checks for compiled extensions =="
python - <<'PY'
import pathlib
import simnibs
import petsc4py

roots = [
    pathlib.Path(simnibs.__file__).resolve().parent,
    pathlib.Path(petsc4py.__file__).resolve().parent,
]

for root in roots:
    print(f"Scanning {root}")
    for so in root.rglob("*.so"):
        print(so)
PY

echo "== CLI availability checks =="
for cmd in simnibs charm meshmesh msh2nii nii2msh mni2subject subject2mni subject2mni_coords mni2subject_coords; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "FOUND: $cmd -> $(command -v "$cmd")"
    else
        echo "MISSING: $cmd"
    fi
done

echo "== Strong PETSc/SimNIBS import test =="
python - <<'PY'
from petsc4py import PETSc
import simnibs
from simnibs.simulation import fem
print("Imported simnibs.simulation.fem: OK")
PY

echo "All non-GUI smoke tests passed."