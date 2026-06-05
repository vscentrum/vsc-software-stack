#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "== GDAL command-line version =="
gdalinfo --version

echo
echo "== GDAL Python version =="
python - <<'PY'
from osgeo import gdal
print("GDAL VersionInfo:", gdal.VersionInfo())
print("GDAL release:", gdal.VersionInfo("--version"))
PY

echo
echo "== Check required drivers are registered =="
gdalinfo --formats | tee "$tmpdir/formats.txt" >/dev/null

grep -Ei '(^|[[:space:]])netCDF[[:space:]]' "$tmpdir/formats.txt"
grep -Ei 'HDF4' "$tmpdir/formats.txt"

python - <<'PY'
from osgeo import gdal

required = ["netCDF", "HDF4"]
optional = ["HDF4Image"]

for name in required:
    drv = gdal.GetDriverByName(name)
    if drv is None:
        raise SystemExit(f"Missing required GDAL driver: {name}")
    print(f"{name}: {drv.GetDescription()} - {drv.GetMetadataItem('DMD_LONGNAME')}")

for name in optional:
    drv = gdal.GetDriverByName(name)
    if drv is not None:
        print(f"{name}: {drv.GetDescription()} - {drv.GetMetadataItem('DMD_LONGNAME')}")
PY

echo
echo "== Create and read a small netCDF raster through GDAL =="
python - "$tmpdir/test.nc" <<'PY'
import sys
import numpy as np
from osgeo import gdal, osr

out = sys.argv[1]
gdal.UseExceptions()

mem = gdal.GetDriverByName("MEM").Create("", 16, 12, 1, gdal.GDT_Float32)
arr = np.arange(16 * 12, dtype=np.float32).reshape(12, 16)
mem.GetRasterBand(1).WriteArray(arr)
mem.SetGeoTransform((-10.0, 0.5, 0.0, 50.0, 0.0, -0.5))

srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
mem.SetProjection(srs.ExportToWkt())

drv = gdal.GetDriverByName("netCDF")
if drv is None:
    raise SystemExit("netCDF driver not available")

ds = drv.CreateCopy(out, mem)
if ds is None:
    raise SystemExit("Failed to create netCDF test file")
ds = None
mem = None

ds = gdal.Open(out)
if ds is None:
    raise SystemExit("Failed to reopen netCDF test file")

band = ds.GetRasterBand(1)
data = band.ReadAsArray()
if data is None or data.shape != (12, 16):
    raise SystemExit(f"Unexpected netCDF raster shape: {None if data is None else data.shape}")

print("Created and reopened:", out)
print("Raster size:", ds.RasterXSize, ds.RasterYSize)
print("Checksum:", band.Checksum())
PY

gdalinfo "$tmpdir/test.nc" >/dev/null

echo
echo "== Optional diagnostic: HDF4 legacy netcdf.h visibility =="
if [[ -n "${EBROOTHDF:-}" && -e "$EBROOTHDF/include/hdf/netcdf.h" ]]; then
    echo "HDF4 legacy header exists: $EBROOTHDF/include/hdf/netcdf.h"
fi
if [[ -n "${EBROOTNETCDF:-}" && -e "$EBROOTNETCDF/include/netcdf.h" ]]; then
    echo "netCDF-C header exists: $EBROOTNETCDF/include/netcdf.h"
fi

echo
echo "GDAL netCDF/HDF4 smoke test passed."