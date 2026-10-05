#!/usr/bin/env bash
set -euo pipefail

# Cactus EasyBuild smoke test
# Run after loading the Cactus module, for example:
#   module load Cactus/3.3.0-foss-2025a
#   bash cactus-smoketest.sh
#
# Optional:
#   CACTUS_SMOKE_CORES=4 bash cactus-smoketest.sh
#   CACTUS_SMOKE_KEEP=1 bash cactus-smoketest.sh   # keep temporary files on success

EXPECTED_CACTUS_VERSION="3.3.0"
EXPECTED_NETWORKX_VERSION="2.8"
EXPECTED_TOIL_VERSION="9.5.0"

CORES="${CACTUS_SMOKE_CORES:-2}"
KEEP="${CACTUS_SMOKE_KEEP:-0}"

die() {
    echo "[FAIL] $*" >&2
    exit 1
}

ok() {
    echo "[ OK ] $*"
}

section() {
    echo
    echo "=== $* ==="
}

command -v python >/dev/null 2>&1 || die "python is not in PATH"
command -v cactus >/dev/null 2>&1 || die "cactus is not in PATH"

ROOT="${EBROOTCACTUS:-}"
[[ -n "${ROOT}" ]] || die "EBROOTCACTUS is not set; load the Cactus EasyBuild module first"
[[ -d "${ROOT}" ]] || die "EBROOTCACTUS does not exist: ${ROOT}"

section "Module and version checks"
echo "EBROOTCACTUS=${ROOT}"
echo "python=$(command -v python)"
echo "cactus=$(command -v cactus)"

ROOT_REAL="$(readlink -f "${ROOT}")"
CACTUS_REAL="$(readlink -f "$(command -v cactus)")"

echo "canonical EBROOTCACTUS=${ROOT_REAL}"
echo "canonical cactus=${CACTUS_REAL}"

case "${CACTUS_REAL}" in
    "${ROOT_REAL}"/*) ;;
    *) die "cactus does not resolve inside EBROOTCACTUS" ;;
esac

python - <<PY
import importlib
import importlib.metadata as md
import sys

expected = {
    "Cactus": "${EXPECTED_CACTUS_VERSION}",
    "networkx": "${EXPECTED_NETWORKX_VERSION}",
    "toil": "${EXPECTED_TOIL_VERSION}",
}

for dist, want in expected.items():
    got = md.version(dist)
    if got != want:
        raise SystemExit(f"{dist}: expected {want}, found {got}")
    print(f"[ OK ] {dist} {got}")

# sonLib is intentionally installed from Cactus's bundled submodule rather than PyPI.
sonlib_version = md.version("sonLib")
print(f"[ OK ] sonLib distribution {sonlib_version}")

for module in ("cactus", "sonLib", "networkx", "toil", "Bio", "pysam"):
    importlib.import_module(module)
    print(f"[ OK ] import {module}")

print(f"[ OK ] Python {sys.version.split()[0]}")
PY

section "Python dependency consistency"
python -m pip check
ok "pip check"

section "Python CLI entry points"
python_clis=(
    cactus
    cactus-prepare
    cactus-preprocess
    cactus-blast
    cactus-align
    cactus-hal2maf
    cactus-pangenome
)

for exe in "${python_clis[@]}"; do
    command -v "${exe}" >/dev/null 2>&1 || die "missing CLI: ${exe}"
    "${exe}" --help >/dev/null 2>&1 || die "${exe} --help failed"
    ok "${exe}"
done

section "Core native executables"
native_clis=(
    cactus_consolidated
    halStats
    halValidate
    lastz
)

for exe in "${native_clis[@]}"; do
    command -v "${exe}" >/dev/null 2>&1 || die "missing native executable: ${exe}"
    ok "${exe}: $(command -v "${exe}")"
done

section "Native shared-library resolution"
ldd_fail=0
while IFS= read -r -d '' exe; do
    ldd_out="$(ldd "${exe}" 2>&1 || true)"
    if grep -q 'not found' <<<"${ldd_out}"; then
        echo "[FAIL] unresolved libraries for ${exe}" >&2
        echo "${ldd_out}" | grep 'not found' >&2
        ldd_fail=1
    fi
done < <(find -L "${ROOT}/bin" -maxdepth 1 -type f -perm -111 -print0)