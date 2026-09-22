#!/bin/bash

set -eo pipefail

PV_MODULE="${PV_MODULE:-ParaView/6.1.1-foss-2026.1}"
EXPECTED_VERSION="6.1.1"

echo "=== ParaView ${EXPECTED_VERSION} smoke test ==="

if ! type module >/dev/null 2>&1; then
    echo "[FAIL] Environment Modules/Lmod is not available"
    exit 1
fi

module load "${PV_MODULE}"

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/paraview-smoketest.XXXXXX")"
export PV_SMOKE_DIR="${WORKDIR}"

cleanup() {
    rc=$?
    if [ "${KEEP_TMP:-0}" = "1" ] || [ "${rc}" -ne 0 ]; then
        echo "[INFO] Test files kept in ${WORKDIR}"
    else
        rm -rf "${WORKDIR}"
    fi
}
trap cleanup EXIT

ok() {
    echo "[OK] $*"
}

fail() {
    echo "[FAIL] $*"
    exit 1
}

echo
echo "--- Executables ---"

for exe in paraview pvpython pvbatch pvserver; do
    command -v "${exe}" >/dev/null 2>&1 || fail "${exe} not found"
    echo "[OK] ${exe}: $(command -v "${exe}")"
done

echo
echo "--- Version ---"

version_output="$(pvpython --version 2>&1)"
echo "${version_output}"

echo "${version_output}" | grep -F "${EXPECTED_VERSION}" >/dev/null ||
    fail "Expected ParaView ${EXPECTED_VERSION}"

ok "ParaView version is ${EXPECTED_VERSION}"

echo
echo "--- Python / VTK / I/O / OpenFOAM / Catalyst ---"

cat > "${WORKDIR}/core_test.py" <<'PY'
import os

from paraview import servermanager
from paraview.simple import (
    Contour,
    Delete,
    GetParaViewSourceVersion,
    OpenDataFile,
    OpenFOAMReader,
    SaveData,
    Wavelet,
)

print("[INFO] " + GetParaViewSourceVersion())

version = (
    servermanager.vtkSMProxyManager.GetVersionMajor(),
    servermanager.vtkSMProxyManager.GetVersionMinor(),
)
assert version == (6, 1), f"Unexpected ParaView version: {version}"
print("[OK] ParaView Python API")

wavelet = Wavelet()
wavelet.UpdatePipeline()

wavelet_data = servermanager.Fetch(wavelet)
assert wavelet_data is not None
assert wavelet_data.GetNumberOfPoints() > 0
print(
    "[OK] Wavelet source: "
    f"{wavelet_data.GetNumberOfPoints()} points, "
    f"{wavelet_data.GetNumberOfCells()} cells"
)

contour = Contour(Input=wavelet)
contour.ContourBy = ["POINTS", "RTData"]
contour.Isosurfaces = [157.0]
contour.UpdatePipeline()

contour_data = servermanager.Fetch(contour)
assert contour_data is not None
assert contour_data.GetNumberOfPoints() > 0
assert contour_data.GetNumberOfCells() > 0

npoints = contour_data.GetNumberOfPoints()
ncells = contour_data.GetNumberOfCells()

print(f"[OK] Contour filter: {npoints} points, {ncells} cells")

outfile = os.path.join(os.environ["PV_SMOKE_DIR"], "contour.vtp")
SaveData(outfile, proxy=contour)

assert os.path.isfile(outfile)
assert os.path.getsize(outfile) > 0
print(f"[OK] VTK XML writer: {outfile}")

reader = OpenDataFile(outfile)
assert reader is not None
reader.UpdatePipeline()

read_data = servermanager.Fetch(reader)
assert read_data is not None
assert read_data.GetNumberOfPoints() == npoints
assert read_data.GetNumberOfCells() == ncells

print("[OK] VTK XML reader")

assert OpenFOAMReader is not None
print("[OK] OpenFOAMReader proxy is available")

try:
    import catalyst
except ImportError as err:
    raise RuntimeError(f"Standalone Catalyst Python module unavailable: {err}")

print("[OK] ParaView-Catalyst Python module")

try:
    from paraview import catalyst as paraview_catalyst
    assert hasattr(paraview_catalyst, "Options")
except Exception as err:
    raise RuntimeError(f"ParaView Catalyst API unavailable: {err}")

print("[OK] paraview.catalyst API")

Delete(reader)
Delete(contour)
Delete(wavelet)

print("=== Core ParaView test PASS ===")
PY

pvpython "${WORKDIR}/core_test.py" || fail "Core ParaView test"
ok "Core ParaView functionality"

echo
echo "--- Off-screen rendering ---"

cat > "${WORKDIR}/render_test.py" <<'PY'
import os

from paraview.simple import (
    CreateView,
    GetOpenGLInformation,
    Render,
    SaveScreenshot,
    Show,
    Sphere,
)

outfile = os.path.join(os.environ["PV_SMOKE_DIR"], "render.png")

sphere = Sphere(ThetaResolution=32, PhiResolution=32)

view = CreateView("RenderView")
view.ViewSize = [400, 300]

Show(sphere, view)
Render(view)

SaveScreenshot(
    outfile,
    view,
    ImageResolution=[400, 300],
)

assert os.path.isfile(outfile)
assert os.path.getsize(outfile) > 1000

print(f"[OK] Off-screen rendering: {outfile}")
print(f"[OK] Screenshot size: {os.path.getsize(outfile)} bytes")

try:
    info = GetOpenGLInformation()

    for name in ("Vendor", "Renderer", "Version"):
        method = getattr(info, "Get" + name, None)
        if method:
            print(f"[INFO] OpenGL {name}: {method()}")
except Exception as err:
    print(f"[INFO] OpenGL information unavailable: {err}")

print("=== Rendering test PASS ===")
PY

pvbatch "${WORKDIR}/render_test.py" || fail "Off-screen rendering"
ok "Off-screen rendering"

echo
echo "--- MPI pvbatch ---"

cat > "${WORKDIR}/mpi_test.py" <<'PY'
from vtkmodules.vtkParallelCore import vtkMultiProcessController
from paraview.simple import Wavelet

controller = vtkMultiProcessController.GetGlobalController()

assert controller is not None, "No global MPI controller"

size = controller.GetNumberOfProcesses()
rank = controller.GetLocalProcessId()

assert size == 2, f"Expected 2 MPI ranks, got {size}"

wavelet = Wavelet()
wavelet.UpdatePipeline()

if rank == 0:
    print(f"[OK] ParaView MPI controller: {size} ranks")
    print("[OK] Parallel pipeline execution")
    print("=== MPI test PASS ===")
PY

if command -v mpirun >/dev/null 2>&1; then
    mpirun -np 2 pvbatch --sym "${WORKDIR}/mpi_test.py" ||
        fail "MPI pvbatch test"
    ok "MPI pvbatch with 2 ranks"
else
    fail "mpirun not found although ParaView is expected to use MPI"
fi

echo
echo "--- Binary startup checks ---"

pvserver --version 2>&1 | grep -F "${EXPECTED_VERSION}" >/dev/null ||
    fail "pvserver version check"

ok "pvserver"

paraview --version 2>&1 | grep -F "${EXPECTED_VERSION}" >/dev/null ||
    fail "paraview version check"

ok "ParaView GUI executable"

echo
echo "=========================================="
echo "=== PASS: ParaView ${EXPECTED_VERSION} ==="
echo "=========================================="