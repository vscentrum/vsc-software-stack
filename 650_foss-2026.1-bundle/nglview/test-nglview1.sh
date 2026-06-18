#!/usr/bin/env bash
set -euo pipefail

echo "== nglview / MD stack smoke test =="
echo "Python: $(command -v python)"
python --version
echo

echo "== Jupyter command checks =="
command -v jupyter
jupyter --version
echo

echo "== JupyterLab / Notebook versions =="
jupyter lab --version
jupyter notebook --version
echo

echo "== Jupyter paths =="
jupyter --paths
echo

echo "== JupyterLab extensions =="
jupyter labextension list || true
echo

echo "== Jupyter server extensions =="
jupyter server extension list || true
echo

echo "== Python package/API checks =="
python - <<'EOF'
import os
import sys
import json
import tempfile
import subprocess
from io import StringIO
from pathlib import Path
from importlib import import_module
from importlib.metadata import version, PackageNotFoundError

def dist_version(dist, module=None):
    try:
        return version(dist)
    except PackageNotFoundError:
        if module:
            mod = import_module(module)
            return getattr(mod, "__version__", "unknown")
        return "not installed"

def check_import(label, module, dist=None):
    mod = import_module(module)
    ver = dist_version(dist or module, module)
    print(f"{label:24s}: OK ({ver})")
    return mod

print("Python executable:", sys.executable)
print("Python version:", sys.version.replace("\n", " "))
print("EB_ENV_JUPYTER_ROOT:", os.environ.get("EB_ENV_JUPYTER_ROOT", "<unset>"))
print()

np = check_import("NumPy", "numpy", "numpy")
pd = check_import("pandas", "pandas", "pandas")
ipywidgets = check_import("ipywidgets", "ipywidgets", "ipywidgets")
jupyterlab = check_import("JupyterLab", "jupyterlab", "jupyterlab")
notebook = check_import("Notebook", "notebook", "notebook")
check_import("jupyterlab_widgets", "jupyterlab_widgets", "jupyterlab_widgets")
check_import("nglview", "nglview", "nglview")
check_import("ASE", "ase", "ase")
check_import("MDAnalysis", "MDAnalysis", "MDAnalysis")
check_import("MDAnalysisTests", "MDAnalysisTests", "MDAnalysisTests")
check_import("MDTraj", "mdtraj", "mdtraj")
check_import("Biopython", "Bio", "biopython")
check_import("Seaborn", "seaborn", "seaborn")
check_import("matplotlib", "matplotlib", "matplotlib")
check_import("scikit-learn", "sklearn", "scikit-learn")
check_import("GridDataFormats", "gridData", "GridDataFormats")
check_import("mrcfile", "mrcfile", "mrcfile")
check_import("mmtf-python", "mmtf", "mmtf-python")
check_import("mda_xdrlib", "mda_xdrlib", "mda_xdrlib")
check_import("tidynamics", "tidynamics", "tidynamics")
print()

import numpy as np
import nglview as nv
from nglview import NGLWidget

def check_ngl_widget(label, widget):
    assert isinstance(widget, NGLWidget), f"{label}: expected NGLWidget, got {type(widget)}"
    state = widget.get_state()
    assert isinstance(state, dict), f"{label}: widget state is not a dict"
    bundle = widget._repr_mimebundle_()
    assert bundle is not None, f"{label}: no MIME bundle returned"
    print(f"{label:24s}: OK ({type(widget).__name__})")

print("== nglview core widget ==")
w = nv.NGLWidget()
check_ngl_widget("empty NGLWidget", w)

print()
print("== nglview + ASE adaptor ==")
from ase import Atoms
atoms = Atoms(
    "OH2",
    positions=[
        [0.0000, 0.0000, 0.0000],
        [0.9572, 0.0000, 0.0000],
        [-0.2390, 0.9270, 0.0000],
    ],
)
w = nv.show_ase(atoms)
check_ngl_widget("nglview.show_ase", w)

print()
print("== nglview + MDTraj adaptor ==")
import mdtraj as md
top = md.Topology()
chain = top.add_chain()
residue = top.add_residue("HOH", chain)
o = top.add_atom("O", md.element.oxygen, residue)
h1 = top.add_atom("H1", md.element.hydrogen, residue)
h2 = top.add_atom("H2", md.element.hydrogen, residue)
top.add_bond(o, h1)
top.add_bond(o, h2)
xyz = np.array(
    [[
        [0.0000, 0.0000, 0.0000],
        [0.09572, 0.0000, 0.0000],
        [-0.02390, 0.09270, 0.0000],
    ]],
    dtype=np.float32,
)
traj = md.Trajectory(xyz=xyz, topology=top)
assert traj.n_atoms == 3
assert traj.n_frames == 1
w = nv.show_mdtraj(traj)
check_ngl_widget("nglview.show_mdtraj", w)

print()
print("== nglview + MDAnalysis adaptor ==")
import MDAnalysis as mda
from MDAnalysis.analysis.rms import rmsd
u = mda.Universe.empty(
    3,
    n_residues=1,
    atom_resindex=[0, 0, 0],
    trajectory=True,
)
u.add_TopologyAttr("names", ["O", "H1", "H2"])
u.add_TopologyAttr("types", ["O", "H", "H"])
u.add_TopologyAttr("resnames", ["HOH"])
u.add_TopologyAttr("resids", [1])
u.atoms.positions = np.array(
    [
        [0.0000, 0.0000, 0.0000],
        [0.9572, 0.0000, 0.0000],
        [-0.2390, 0.9270, 0.0000],
    ],
    dtype=np.float32,
)
assert len(u.atoms) == 3
assert rmsd(u.atoms.positions, u.atoms.positions) == 0.0
w = nv.show_mdanalysis(u)
check_ngl_widget("nglview.show_mdanalysis", w)

print()
print("== nglview + Biopython adaptor ==")
from Bio.PDB import PDBParser
pdb_text = """\
ATOM      1  O   HOH A   1       0.000   0.000   0.000  1.00 20.00           O
ATOM      2  H1  HOH A   1       0.957   0.000   0.000  1.00 20.00           H
ATOM      3  H2  HOH A   1      -0.239   0.927   0.000  1.00 20.00           H
TER
END
"""
structure = PDBParser(QUIET=True).get_structure("water", StringIO(pdb_text))
assert len(list(structure.get_atoms())) == 3
w = nv.show_biopython(structure)
check_ngl_widget("nglview.show_biopython", w)

print()
print("== ASE basic IO/functionality ==")
from ase.io import write
with tempfile.TemporaryDirectory() as tmpdir:
    xyz_path = Path(tmpdir) / "water.xyz"
    write(xyz_path, atoms)
    assert xyz_path.exists()
    assert xyz_path.stat().st_size > 0
print("ASE write XYZ           : OK")

print()
print("== MDAnalysis basic trajectory functionality ==")
coords = np.array(
    [
        [[0.0, 0.0, 0.0], [0.9, 0.0, 0.0], [-0.2, 0.9, 0.0]],
        [[0.1, 0.0, 0.0], [1.0, 0.0, 0.0], [-0.1, 0.9, 0.0]],
    ],
    dtype=np.float32,
)
u2 = mda.Universe.empty(3, n_residues=1, atom_resindex=[0, 0, 0])
u2.add_TopologyAttr("names", ["O", "H1", "H2"])
u2.add_TopologyAttr("resnames", ["HOH"])
u2.load_new(coords, order="fac")
assert len(u2.trajectory) == 2
print("MDAnalysis MemoryReader : OK")

print()
print("== Seaborn/matplotlib non-interactive plotting ==")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
with tempfile.TemporaryDirectory() as tmpdir:
    png_path = Path(tmpdir) / "seaborn_test.png"
    ax = sns.scatterplot(x=[0, 1, 2], y=[0, 1, 4])
    ax.figure.savefig(png_path)
    plt.close(ax.figure)
    assert png_path.exists()
    assert png_path.stat().st_size > 0
print("Seaborn Agg plot        : OK")

print()
print("== nglview installed frontend assets ==")
nglview_dir = Path(nv.__file__).resolve().parent
print("nglview package dir:", nglview_dir)
frontend_candidates = []
for pattern in ("**/package.json", "**/*.js", "**/*.css"):
    frontend_candidates.extend(nglview_dir.glob(pattern))
frontend_candidates = [p for p in frontend_candidates if "__pycache__" not in str(p)]
print("frontend asset count:", len(frontend_candidates))
assert frontend_candidates, "No nglview frontend assets found under package directory"
for path in frontend_candidates[:10]:
    print("  ", path.relative_to(nglview_dir))
if len(frontend_candidates) > 10:
    print(f"   ... {len(frontend_candidates) - 10} more")

print()
print("All Python/API checks passed.")
EOF

echo
echo "== pip consistency check =="
python -m pip check

echo
echo "== nglview/JupyterLab frontend visibility check =="
if jupyter labextension list 2>&1 | grep -Eiq 'ngl|nglview|nglview-js-widgets'; then
    echo "nglview JupyterLab extension appears in labextension list: OK"
else
    echo "WARNING: no nglview-like entry found in 'jupyter labextension list'"
    echo "The Python package and frontend assets were found, but verify the widget in a browser."
fi

echo
echo "== smoke test completed successfully =="