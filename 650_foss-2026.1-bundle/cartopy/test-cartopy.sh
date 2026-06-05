#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

export MPLBACKEND=Agg
out_png="$tmpdir/cartopy_smoketest.png"

echo "== Cartopy/Python package versions =="

python - "$out_png" <<'PY'
import sys
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import cartopy
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
import shapely
from shapely.geometry import box
import pyproj

out_png = sys.argv[1]

print("cartopy:", cartopy.__version__)
print("matplotlib:", matplotlib.__version__)
print("numpy:", np.__version__)
print("shapely:", shapely.__version__)
print("pyproj:", pyproj.__version__)

pc = ccrs.PlateCarree()
merc = ccrs.Mercator()
pts = merc.transform_points(pc, np.array([0.0, 10.0, 20.0]), np.array([45.0, 50.0, 55.0]))

if pts.shape != (3, 3):
    raise SystemExit(f"Unexpected transformed point shape: {pts.shape}")
if not np.isfinite(pts).all():
    raise SystemExit("Projection transform produced non-finite values")

geom = box(-10.0, 45.0, 20.0, 55.0)
feature = ShapelyFeature([geom], pc, facecolor="none")

fig = plt.figure(figsize=(6, 4))
ax = plt.axes(projection=pc)
ax.set_extent([-20, 30, 35, 65], crs=pc)
ax.add_feature(feature)
ax.gridlines(draw_labels=False)
ax.plot([0, 10, 20], [45, 50, 55], marker="o", transform=pc)
ax.set_title("Cartopy smoke test")
fig.savefig(out_png, dpi=100, bbox_inches="tight")
plt.close(fig)

print("Projection transform OK")
print("Plot written to:", out_png)
PY

test -s "$out_png"
file "$out_png"

echo
echo "Cartopy smoke test passed."