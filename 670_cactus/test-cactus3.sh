#!/usr/bin/env bash
set -euo pipefail

# Cactus EasyBuild smoke test
#
# Focus:
#   - validate Cactus 3.3.0 with NetworkX 3.5
#   - verify NetworkX is loaded from the expected EasyBuild dependency
#   - verify the installed Cactus metadata accepts NetworkX 3.5
#   - exercise the progressive tree/outgroup code that uses NetworkX
#   - run a small real Cactus alignment using local binaries only
#
# Run after loading the Cactus module, for example:
#
#   module load Cactus/3.3.0-foss-2025a
#   bash cactus-smoketest.sh
#
# Optional:
#
#   CACTUS_SMOKE_CORES=4 bash cactus-smoketest.sh
#
# Keep temporary files even on success:
#
#   CACTUS_SMOKE_KEEP=1 bash cactus-smoketest.sh

EXPECTED_CACTUS_VERSION="3.3.0"
EXPECTED_NETWORKX_VERSION="3.5"
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


command -v python >/dev/null 2>&1 ||
    die "python is not in PATH"

command -v cactus >/dev/null 2>&1 ||
    die "cactus is not in PATH"


ROOT="${EBROOTCACTUS:-}"
NETWORKX_ROOT="${EBROOTNETWORKX:-}"

[[ -n "${ROOT}" ]] ||
    die "EBROOTCACTUS is not set; load the Cactus EasyBuild module first"

[[ -d "${ROOT}" ]] ||
    die "EBROOTCACTUS does not exist: ${ROOT}"

[[ -n "${NETWORKX_ROOT}" ]] ||
    die "EBROOTNETWORKX is not set; the NetworkX EasyBuild dependency is not loaded"

[[ -d "${NETWORKX_ROOT}" ]] ||
    die "EBROOTNETWORKX does not exist: ${NETWORKX_ROOT}"


ROOT_REAL="$(readlink -f "${ROOT}")"
NETWORKX_ROOT_REAL="$(readlink -f "${NETWORKX_ROOT}")"
CACTUS_REAL="$(readlink -f "$(command -v cactus)")"


export EXPECTED_CACTUS_VERSION
export EXPECTED_NETWORKX_VERSION
export EXPECTED_TOIL_VERSION
export ROOT_REAL
export NETWORKX_ROOT_REAL


section "Module and executable location"

echo "EBROOTCACTUS=${ROOT}"
echo "canonical EBROOTCACTUS=${ROOT_REAL}"

echo "EBROOTNETWORKX=${NETWORKX_ROOT}"
echo "canonical EBROOTNETWORKX=${NETWORKX_ROOT_REAL}"

echo "python=$(command -v python)"
echo "cactus=$(command -v cactus)"
echo "canonical cactus=${CACTUS_REAL}"


case "${CACTUS_REAL}" in
    "${ROOT_REAL}"/*) ;;
    *) die "cactus does not resolve inside EBROOTCACTUS" ;;
esac

ok "cactus resolves inside EBROOTCACTUS"


section "Python package and NetworkX checks"

python - <<'PY'
import importlib
import importlib.metadata as md
import os
import sys

from packaging.requirements import Requirement
from packaging.version import Version

import cactus
import networkx


cactus_root = os.path.realpath(os.environ["ROOT_REAL"])
networkx_root = os.path.realpath(os.environ["NETWORKX_ROOT_REAL"])


expected = {
    "Cactus": os.environ["EXPECTED_CACTUS_VERSION"],
    "networkx": os.environ["EXPECTED_NETWORKX_VERSION"],
    "toil": os.environ["EXPECTED_TOIL_VERSION"],
}


for dist, want in expected.items():
    got = md.version(dist)

    if got != want:
        raise SystemExit(
            f"{dist}: expected {want}, found {got}"
        )

    print(f"[ OK ] {dist} {got}")


# Verify that Cactus and NetworkX are imported from the expected
# EasyBuild installation prefixes.
for name, module, expected_root in (
    ("cactus", cactus, cactus_root),
    ("networkx", networkx, networkx_root),
):
    module_path = os.path.realpath(module.__file__)

    try:
        common = os.path.commonpath(
            (expected_root, module_path)
        )
    except ValueError:
        common = ""

    if common != expected_root:
        raise SystemExit(
            f"{name} is not imported from the expected "
            f"EasyBuild prefix: {module_path}; "
            f"expected under {expected_root}"
        )

    print(
        f"[ OK ] {name} loaded from {module_path}"
    )


# Check NetworkX's own reported runtime version.
if networkx.__version__ != os.environ["EXPECTED_NETWORKX_VERSION"]:
    raise SystemExit(
        f"networkx.__version__: expected "
        f"{os.environ['EXPECTED_NETWORKX_VERSION']}, "
        f"found {networkx.__version__}"
    )

print(
    f"[ OK ] networkx.__version__ = "
    f"{networkx.__version__}"
)


# Verify that the NetworkX requirement recorded in the installed
# Cactus metadata accepts the NetworkX 3.x dependency supplied by
# EasyBuild.
requirements = md.requires("Cactus") or []

networkx_requirements = []

for requirement_string in requirements:
    requirement = Requirement(requirement_string)

    if requirement.name.lower() == "networkx":
        networkx_requirements.append(requirement)


if len(networkx_requirements) != 1:
    raise SystemExit(
        "Expected exactly one Cactus NetworkX requirement, "
        f"found: {networkx_requirements}"
    )


networkx_requirement = networkx_requirements[0]
networkx_version = Version(networkx.__version__)

print(
    f"[INFO] installed Cactus requirement: "
    f"{networkx_requirement}"
)


if networkx_version not in networkx_requirement.specifier:
    raise SystemExit(
        f"Cactus requirement {networkx_requirement} "
        f"does not accept NetworkX {networkx_version}"
    )


print(
    f"[ OK ] Cactus metadata accepts "
    f"NetworkX {networkx_version}"
)


# sonLib is intentionally installed from Cactus's bundled
# submodule rather than from PyPI.
sonlib_version = md.version("sonLib")

print(
    f"[ OK ] sonLib distribution "
    f"{sonlib_version}"
)


# Explicitly import the progressive Cactus modules that exercise
# tree/outgroup functionality using NetworkX.
modules = (
    "cactus",
    "sonLib",
    "networkx",
    "toil",
    "Bio",
    "pysam",
    "cactus.progressive.multiCactusTree",
    "cactus.progressive.outgroup",
    "cactus.progressive.cactus_progressive",
)


for module in modules:
    imported = importlib.import_module(module)
    path = getattr(imported, "__file__", None)

    if path:
        print(
            f"[ OK ] import {module}: {path}"
        )
    else:
        print(
            f"[ OK ] import {module}"
        )


print(
    f"[ OK ] Python "
    f"{sys.version.split()[0]}"
)
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
    command -v "${exe}" >/dev/null 2>&1 ||
        die "missing CLI: ${exe}"

    "${exe}" --help >/dev/null 2>&1 ||
        die "${exe} --help failed"

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
    command -v "${exe}" >/dev/null 2>&1 ||
        die "missing native executable: ${exe}"

    ok "${exe}: $(command -v "${exe}")"
done


section "Native shared-library resolution"

ldd_fail=0


while IFS= read -r -d '' exe; do
    ldd_out="$(ldd "${exe}" 2>&1 || true)"

    if grep -q 'not found' <<<"${ldd_out}"; then
        echo \
            "[FAIL] unresolved libraries for ${exe}" \
            >&2

        grep 'not found' <<<"${ldd_out}" >&2

        ldd_fail=1
    fi
done < <(
    find -L "${ROOT}/bin" \
        -maxdepth 1 \
        -type f \
        -perm -111 \
        -print0
)


[[ "${ldd_fail}" -eq 0 ]] ||
    die "unresolved shared libraries detected"

ok "no unresolved shared libraries found"


section "Create local NetworkX/progressive Cactus test data"

TMP="$(
    mktemp -d \
        "${TMPDIR:-/tmp}/cactus-smoke.XXXXXX"
)"


cleanup() {
    rc=$?

    if [[ "${KEEP}" == "1" || "${rc}" -ne 0 ]]; then
        echo
        echo \
            "[INFO] keeping smoke-test directory: " \
            "${TMP}"
    else
        rm -rf "${TMP}"
    fi
}


trap cleanup EXIT


echo "temporary directory: ${TMP}"

export SMOKE_TMP="${TMP}"


python - <<'PY'
import os
import random


outdir = os.environ["SMOKE_TMP"]

rng = random.Random(123456)

length = 12000
alphabet = "ACGT"

base = [
    rng.choice(alphabet)
    for _ in range(length)
]


def mutated_sequence(source, offset):
    seq = list(source)

    # Deterministic sparse substitutions. The four genomes
    # therefore remain closely related but are not
    # byte-identical.
    for pos in range(
        offset,
        len(seq),
        101,
    ):
        old = seq[pos]

        choices = [
            base
            for base in alphabet
            if base != old
        ]

        seq[pos] = choices[
            (pos + offset) % len(choices)
        ]

    return "".join(seq)


sequences = {
    "A": mutated_sequence(base, 3),
    "B": mutated_sequence(base, 17),
    "C": mutated_sequence(base, 41),
    "D": mutated_sequence(base, 67),
}


for genome, sequence in sequences.items():
    path = os.path.join(
        outdir,
        f"{genome}.fa",
    )

    with open(path, "w") as handle:
        handle.write(">chr1\n")

        for i in range(
            0,
            len(sequence),
            80,
        ):
            handle.write(
                sequence[i:i + 80] + "\n"
            )

    print(
        f"[ OK ] wrote {path}: "
        f"{len(sequence)} bp"
    )
PY


SEQFILE="${TMP}/seqfile.txt"


cat > "${SEQFILE}" <<EOF
((A:0.05,B:0.05):0.05,(C:0.05,D:0.05):0.05);
A	${TMP}/A.fa
B	${TMP}/B.fa
C	${TMP}/C.fa
D	${TMP}/D.fa
EOF


echo
cat "${SEQFILE}"

ok "generated four-genome binary tree"


section "Progressive planning / NetworkX tree logic"

PREPARE_DIR="${TMP}/prepare"
PREPARE_JOBSTORE="${TMP}/prepare-jobstores"
PREPARE_PLAN="${TMP}/cactus-plan.txt"


mkdir -p "${PREPARE_DIR}"


CACTUS_BINARIES_MODE=local \
CACTUS_DOCKER_MODE=0 \
cactus-prepare \
    "${SEQFILE}" \
    --outDir "${PREPARE_DIR}" \
    --outSeqFile "${PREPARE_DIR}/seqfile.txt" \
    --outHal "${PREPARE_DIR}/out.hal" \
    --jobStore "${PREPARE_JOBSTORE}" \
    --cactusOptions "--binariesMode local" \
    > "${PREPARE_PLAN}"


[[ -s "${PREPARE_PLAN}" ]] ||
    die "cactus-prepare did not produce a plan"


grep -q 'cactus-preprocess' "${PREPARE_PLAN}" ||
    die \
        "cactus-prepare plan does not contain " \
        "cactus-preprocess"


grep -q 'cactus-blast' "${PREPARE_PLAN}" ||
    die \
        "cactus-prepare plan does not contain " \
        "cactus-blast"


grep -q 'cactus-align' "${PREPARE_PLAN}" ||
    die \
        "cactus-prepare plan does not contain " \
        "cactus-align"


[[ -s "${PREPARE_DIR}/seqfile.txt" ]] ||
    die \
        "cactus-prepare did not create the " \
        "annotated seqfile"


ok \
    "cactus-prepare successfully processed " \
    "the four-genome tree"

ok "progressive execution plan generated"


section "Real local progressive Cactus workflow"

JOBSTORE="${TMP}/jobstore"
WORKDIR="${TMP}/toil-work"
OUT_HAL="${TMP}/networkx-smoke.hal"
CACTUS_LOG="${TMP}/cactus.log"


mkdir -p "${WORKDIR}"


echo "Running Cactus with ${CORES} cores..."
echo "log: ${CACTUS_LOG}"


if ! CACTUS_BINARIES_MODE=local \
     CACTUS_DOCKER_MODE=0 \
     cactus \
        "${JOBSTORE}" \
        "${SEQFILE}" \
        "${OUT_HAL}" \
        --binariesMode local \
        --batchSystem single_machine \
        --maxCores "${CORES}" \
        --retryCount 0 \
        --workDir "${WORKDIR}" \
        > "${CACTUS_LOG}" 2>&1
then
    echo
    echo \
        "===== last 200 lines of Cactus log =====" \
        >&2

    tail -n 200 \
        "${CACTUS_LOG}" \
        >&2 || true

    die "Cactus progressive workflow failed"
fi


[[ -s "${OUT_HAL}" ]] ||
    die \
        "Cactus did not produce a non-empty " \
        "HAL file"


ok "Cactus progressive alignment completed"


section "HAL validation"

halValidate "${OUT_HAL}" >/dev/null

ok "halValidate"


GENOMES="$(
    halStats \
        --genomes \
        "${OUT_HAL}"
)"


echo "HAL genomes: ${GENOMES}"


read -ra HAL_GENOMES <<<"${GENOMES}"


for genome in A B C D; do
    found=0

    for hal_genome in "${HAL_GENOMES[@]}"; do
        if [[ "${hal_genome}" == "${genome}" ]]; then
            found=1
            break
        fi
    done

    [[ "${found}" -eq 1 ]] ||
        die \
            "input genome ${genome} not present " \
            "in HAL output"

    ok "HAL contains ${genome}"
done


section "NetworkX smoke-test summary"

python - <<'PY'
import importlib.metadata as md

from packaging.requirements import Requirement

import networkx


print(
    f"NetworkX runtime version : "
    f"{networkx.__version__}"
)

print(
    f"NetworkX package path    : "
    f"{networkx.__file__}"
)

print(
    f"Cactus version           : "
    f"{md.version('Cactus')}"
)


requirements = md.requires("Cactus") or []

for requirement_string in requirements:
    requirement = Requirement(
        requirement_string
    )

    if requirement.name.lower() == "networkx":
        print(
            f"Cactus NetworkX metadata : "
            f"{requirement}"
        )
PY


echo

echo \
    "[PASS] Cactus ${EXPECTED_CACTUS_VERSION} " \
    "smoke test completed successfully"

echo \
    "[PASS] NetworkX ${EXPECTED_NETWORKX_VERSION} " \
    "is compatible with the tested Cactus " \
    "progressive workflow"