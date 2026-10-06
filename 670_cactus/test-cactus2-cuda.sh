#!/usr/bin/env bash
set -euo pipefail

# Cactus CUDA EasyBuild smoke test
#
# Run after loading the CUDA-enabled Cactus module on a GPU node, e.g.:
#   module load Cactus/3.3.0-foss-2025a-CUDA-12.8.0
#   bash cactus-cuda-smoketest.sh
#
# Optional:
#   CACTUS_SMOKE_CORES=4 bash cactus-cuda-smoketest.sh
#   CACTUS_SMOKE_KEEP=1 bash cactus-cuda-smoketest.sh

EXPECTED_CACTUS_VERSION="3.3.0"
EXPECTED_NETWORKX_VERSION="2.8"
EXPECTED_TOIL_VERSION="9.5.0"

CORES="${CACTUS_SMOKE_CORES:-2}"
KEEP="${CACTUS_SMOKE_KEEP:-0}"
WORKDIR=""

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

cleanup() {
    rc=$?
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP}" == "1" || ${rc} -ne 0 ]]; then
            echo "[INFO] keeping temporary directory: ${WORKDIR}" >&2
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}
trap cleanup EXIT

command -v python >/dev/null 2>&1 || die "python is not in PATH"
command -v cactus >/dev/null 2>&1 || die "cactus is not in PATH"

ROOT="${EBROOTCACTUS:-}"
[[ -n "${ROOT}" ]] || die "EBROOTCACTUS is not set; load the Cactus module first"
[[ -d "${ROOT}" ]] || die "EBROOTCACTUS does not exist: ${ROOT}"

section "Module and version checks"
echo "EBROOTCACTUS=${ROOT}"
echo "python=$(command -v python)"
echo "cactus=$(command -v cactus)"

ROOT_REAL="$(readlink -f "${ROOT}")"
CACTUS_REAL="$(readlink -f "$(command -v cactus)")"

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

print(f"[ OK ] sonLib distribution {md.version('sonLib')}")

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

section "Core native and GPU executables"
native_clis=(
    cactus_consolidated
    halStats
    halValidate
    lastz
    kegalign
    run_kegalign
    diagonal_partition.py
)

for exe in "${native_clis[@]}"; do
    command -v "${exe}" >/dev/null 2>&1 || die "missing executable: ${exe}"
    ok "${exe}: $(command -v "${exe}")"
done

run_kegalign --help >/dev/null 2>&1 || die "run_kegalign --help failed"
ok "run_kegalign --help"

section "KegAlign runtime tools"
for exe in faToTwoBit mbuffer; do
    command -v "${exe}" >/dev/null 2>&1 || die "missing KegAlign runtime tool: ${exe}"
    ok "${exe}: $(command -v "${exe}")"
done

section "Embedded TBB libraries"
for lib in libtbb.so.2 libtbbmalloc.so.2 libtbbmalloc_proxy.so.2 libtbb_preview.so.2; do
    [[ -e "${ROOT}/lib/${lib}" ]] || die "missing embedded TBB library: ${ROOT}/lib/${lib}"
    ok "${lib}"
done

section "Native shared-library resolution"
# Check only the native binaries that belong to this installation.
# Do not follow arbitrary symlinks from ${ROOT}/bin into /bin or /usr/bin.
elf_clis=(
    cactus_consolidated
    halStats
    halValidate
    lastz
    kegalign
)

for exe in "${elf_clis[@]}"; do
    path="$(command -v "${exe}")"
    real="$(readlink -f "${path}")"

    case "${real}" in
        "${ROOT_REAL}"/*) ;;
        *) die "${exe} resolves outside EBROOTCACTUS: ${real}" ;;
    esac

    if file "${real}" | grep -q 'ELF'; then
        ldd_out="$(ldd "${real}" 2>&1 || true)"
        if grep -q 'not found' <<<"${ldd_out}"; then
            echo "${ldd_out}" | grep 'not found' >&2
            die "unresolved libraries for ${exe}"
        fi
    fi
    ok "ldd ${exe}"
done

section "CUDA and GPU visibility"
command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi is not in PATH"
nvidia-smi -L >/dev/null 2>&1 || die "no usable NVIDIA GPU is visible"
nvidia-smi -L
ok "NVIDIA GPU visible"

if command -v nvcc >/dev/null 2>&1; then
    nvcc --version | tail -n 1
    ok "nvcc available"
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/cactus-cuda-smoke.XXXXXX")"
cd "${WORKDIR}"
echo "workdir=${WORKDIR}"

section "Generate deterministic local test genomes"
python - <<'PY'
from pathlib import Path
import random

rng = random.Random(12345)
bases = "ACGT"
ancestor = [rng.choice(bases) for _ in range(30000)]

def mutated(seq, period, offset):
    out = list(seq)
    for i in range(offset, len(out), period):
        old = out[i]
        out[i] = bases[(bases.index(old) + 1) % 4]
    return "".join(out)

def write_fasta(path, name, seq):
    with open(path, "w") as fh:
        fh.write(f">{name}\n")
        for i in range(0, len(seq), 80):
            fh.write(seq[i:i + 80] + "\n")

write_fasta("A.fa", "A_chr1", mutated(ancestor, 211, 7))
write_fasta("B.fa", "B_chr1", mutated(ancestor, 223, 11))
write_fasta("C.fa", "C_chr1", mutated(ancestor, 197, 17))

wd = Path.cwd()
with open("seqfile.txt", "w") as fh:
    fh.write("((A:0.05,B:0.05):0.05,C:0.1);\n")
    fh.write(f"A {wd / 'A.fa'}\n")
    fh.write(f"B {wd / 'B.fa'}\n")
    fh.write(f"C {wd / 'C.fa'}\n")
PY
ok "generated three 30 kbp FASTA inputs"

section "Direct KegAlign GPU wrapper test"
run_kegalign A.fa B.fa \
    --format=paf:minimap2 \
    --step=1 \
    --ambiguous=iupac,100,100 \
    --ydrop=3000 \
    --num_gpu 1 \
    --num_threads "${CORES}" \
    > kegalign.paf

[[ -s kegalign.paf ]] || die "run_kegalign produced an empty PAF"
awk -F '\t' 'NF >= 12 { found=1; exit } END { exit(found ? 0 : 1) }' kegalign.paf \
    || die "run_kegalign output does not contain a valid-looking PAF record"
ok "run_kegalign completed on GPU and produced PAF output"

section "Progressive Cactus GPU integration test"
cactus jobstore seqfile.txt output.hal \
    --binariesMode local \
    --gpu 1 \
    --lastzCores "${CORES}" \
    --maxCores "${CORES}" \
    --disableProgress

[[ -s output.hal ]] || die "Cactus did not produce output.hal"
halValidate output.hal >/dev/null
ok "halValidate output.hal"

HAL_STATS="$(halStats output.hal)"
echo "${HAL_STATS}"

for genome in A B C; do
    grep -qw "${genome}" <<<"${HAL_STATS}" || die "${genome} is missing from halStats output"
done
ok "HAL contains A, B and C"

section "PASS"
echo "Cactus ${EXPECTED_CACTUS_VERSION} CUDA smoke test passed, including KegAlign and Progressive Cactus --gpu 1."
