#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

python - "$tmpdir" <<'PY'
import os
import sys
import pathlib
import importlib.util
import subprocess

tmpdir = pathlib.Path(sys.argv[1])

import numpy as np
import matplotlib
matplotlib.use("Agg", force=True)

from matplotlib import pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image

import cycler
import kiwisolver
import contourpy

print("Python:", sys.version.split()[0])
print("matplotlib:", matplotlib.__version__)
print("numpy:", np.__version__)
print("Pillow:", Image.__version__)
print("cycler:", cycler.__version__)
print("kiwisolver:", kiwisolver.__version__)
print("contourpy:", contourpy.__version__)
print("backend:", matplotlib.get_backend())

assert matplotlib.__version__ == "3.10.9"
assert matplotlib.get_backend().lower() == "agg"

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
ax.plot(x, np.sin(x), label="sin(x)")
ax.set_title("matplotlib smoke test")
ax.set_xlabel("x")
ax.set_ylabel("sin(x)")
ax.legend()
png = tmpdir / "basic_plot.png"
fig.savefig(png)
plt.close(fig)

img = Image.open(png)
assert img.size[0] > 0 and img.size[1] > 0
print("basic PNG plot:", png)

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
t = np.linspace(0, 4 * np.pi, 100)
ax.plot(np.sin(t), np.cos(t), t)
png3d = tmpdir / "plot_3d.png"
fig.savefig(png3d)
plt.close(fig)
assert png3d.exists() and png3d.stat().st_size > 0
print("3D plot:", png3d)

x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)
Z = np.sin(X ** 2 + Y ** 2)
fig, ax = plt.subplots()
cs = ax.contour(X, Y, Z)
assert len(cs.levels) > 0
contour_png = tmpdir / "contour_plot.png"
fig.savefig(contour_png)
plt.close(fig)
assert contour_png.exists() and contour_png.stat().st_size > 0
print("contour plot:", contour_png)

import matplotlib.tri as tri
rng = np.random.default_rng(123)
points = rng.random((100, 2))
triang = tri.Triangulation(points[:, 0], points[:, 1])
assert triang.triangles.shape[1] == 3
fig, ax = plt.subplots()
ax.triplot(triang)
tri_png = tmpdir / "triangulation_plot.png"
fig.savefig(tri_png)
plt.close(fig)
assert tri_png.exists() and tri_png.stat().st_size > 0
print("triangulation plot:", tri_png)

font = font_manager.findfont("DejaVu Sans")
assert pathlib.Path(font).exists()
print("font lookup:", font)

for modname in ["matplotlib.ft2font", "matplotlib._qhull"]:
    spec = importlib.util.find_spec(modname)
    assert spec is not None, modname
    assert spec.origin is not None, modname
    print(f"{modname}:", spec.origin)

def check_linkage(modname, envvar):
    root = os.environ.get(envvar)
    spec = importlib.util.find_spec(modname)
    if not root or not spec or not spec.origin:
        print(f"skip linkage check for {modname}: {envvar} not set or module not found")
        return
    out = subprocess.check_output(["ldd", spec.origin], text=True)
    print(f"ldd check for {modname} using {envvar}={root}")
    print(out)
    assert root in out, f"{modname} is not linked against {envvar}={root}"

check_linkage("matplotlib.ft2font", "EBROOTFREETYPE")
check_linkage("matplotlib._qhull", "EBROOTQHULL")

print("matplotlib smoke test passed")
PY