#!/bin/bash

set -euo pipefail

EXPECTED_VERSION="4.4.10"

echo "=== DSSP ${EXPECTED_VERSION} smoke test ==="

fail() {
    echo "[FAIL] $*" >&2
    exit 1
}

ok() {
    echo "[OK] $*"
}

# ----------------------------------------------------------------------
# 1. Locate installed mkdssp
# ----------------------------------------------------------------------

command -v mkdssp >/dev/null 2>&1 || fail "mkdssp not found in PATH"

MKDSSP="$(command -v mkdssp)"
echo "[INFO] mkdssp: ${MKDSSP}"

# ----------------------------------------------------------------------
# 2. Version check
#
# Starting the executable already verifies that the patched mcfp target
# was linked into a usable mkdssp binary.
# ----------------------------------------------------------------------

VERSION_OUTPUT="$("${MKDSSP}" --version 2>&1)"

echo "[INFO] ${VERSION_OUTPUT}"

echo "${VERSION_OUTPUT}" | grep -q "${EXPECTED_VERSION}" \
    || fail "Expected DSSP version ${EXPECTED_VERSION}"

ok "DSSP reports version ${EXPECTED_VERSION}"

# ----------------------------------------------------------------------
# 3. Exercise command-line parsing provided by mcfp
# ----------------------------------------------------------------------

"${MKDSSP}" --help >/dev/null 2>&1 \
    || fail "mkdssp --help failed"

ok "mcfp-backed mkdssp command-line parsing works"

# ----------------------------------------------------------------------
# 4. Check dynamic-library resolution
# ----------------------------------------------------------------------

if command -v ldd >/dev/null 2>&1; then
    LDD_OUTPUT="$(ldd "${MKDSSP}")"

    if echo "${LDD_OUTPUT}" | grep -q 'not found'; then
        echo "${LDD_OUTPUT}"
        fail "mkdssp has unresolved shared-library dependencies"
    fi

    ok "All dynamic libraries used by mkdssp are resolved"

    if echo "${LDD_OUTPUT}" | grep -Ei 'mcfp' >/dev/null; then
        echo "[INFO] mcfp runtime linkage:"
        echo "${LDD_OUTPUT}" | grep -Ei 'mcfp'
    else
        echo "[INFO] No separate mcfp shared library in ldd output"
        echo "[INFO] This is OK if mcfp was linked statically"
    fi
fi

# ----------------------------------------------------------------------
# 5. Create a small synthetic protein structure
#
# PDB input is used so the smoke test does not depend on source-tree
# test data. CRYST1 is required for properly formatted PDB input.
# ----------------------------------------------------------------------

TMPDIR_DSSP="$(mktemp -d)"
trap 'rm -rf "${TMPDIR_DSSP}"' EXIT

INPUT_PDB="${TMPDIR_DSSP}/test.pdb"

cat > "${INPUT_PDB}" <<'EOF'
HEADER    DSSP SMOKE TEST
CRYST1   50.000   50.000   50.000  90.00  90.00  90.00 P 1           1
ATOM      1  N   ALA A   1       5.000   5.000   5.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       6.450   5.000   5.000  1.00 20.00           C
ATOM      3  C   ALA A   1       7.050   6.400   5.000  1.00 20.00           C
ATOM      4  O   ALA A   1       6.400   7.400   5.000  1.00 20.00           O
ATOM      5  CB  ALA A   1       7.000   4.200   6.180  1.00 20.00           C
ATOM      6  N   ALA A   2       8.360   6.480   5.000  1.00 20.00           N
ATOM      7  CA  ALA A   2       9.050   7.760   5.000  1.00 20.00           C
ATOM      8  C   ALA A   2      10.560   7.550   5.000  1.00 20.00           C
ATOM      9  O   ALA A   2      11.150   6.480   5.000  1.00 20.00           O
ATOM     10  CB  ALA A   2       8.540   8.570   6.190  1.00 20.00           C
ATOM     11  N   ALA A   3      11.160   8.640   5.000  1.00 20.00           N
ATOM     12  CA  ALA A   3      12.600   8.620   5.000  1.00 20.00           C
ATOM     13  C   ALA A   3      13.120  10.060   5.000  1.00 20.00           C
ATOM     14  O   ALA A   3      12.380  11.020   5.000  1.00 20.00           O
ATOM     15  CB  ALA A   3      13.130   7.810   6.190  1.00 20.00           C
ATOM     16  N   ALA A   4      14.420  10.170   5.000  1.00 20.00           N
ATOM     17  CA  ALA A   4      15.040  11.490   5.000  1.00 20.00           C
ATOM     18  C   ALA A   4      16.570  11.320   5.000  1.00 20.00           C
ATOM     19  O   ALA A   4      17.110  10.200   5.000  1.00 20.00           O
ATOM     20  CB  ALA A   4      14.520  12.300   6.190  1.00 20.00           C
ATOM     21  N   ALA A   5      17.210  12.390   5.000  1.00 20.00           N
ATOM     22  CA  ALA A   5      18.650  12.370   5.000  1.00 20.00           C
ATOM     23  C   ALA A   5      19.170  13.810   5.000  1.00 20.00           C
ATOM     24  O   ALA A   5      18.430  14.770   5.000  1.00 20.00           O
ATOM     25  CB  ALA A   5      19.180  11.560   6.190  1.00 20.00           C
TER
END
EOF

[[ -s "${INPUT_PDB}" ]] || fail "Failed to create synthetic PDB input"

ok "Synthetic PDB test structure created"

# ----------------------------------------------------------------------
# 6. Real PDB -> annotated mmCIF calculation
#
# This is the important mrc-resource test.
#
# We deliberately do NOT specify --mmcif-dictionary. With USE_RSRC=ON,
# the required mmCIF dictionaries should have been embedded into mkdssp
# by mrc_target_resources().
# ----------------------------------------------------------------------

MMCIF_OUTPUT="${TMPDIR_DSSP}/test-dssp.cif"

"${MKDSSP}" \
    "${INPUT_PDB}" \
    "${MMCIF_OUTPUT}"

[[ -s "${MMCIF_OUTPUT}" ]] \
    || fail "Annotated mmCIF output was not created"

grep -q '^data_' "${MMCIF_OUTPUT}" \
    || fail "Output does not look like valid mmCIF"

grep -q '_atom_site' "${MMCIF_OUTPUT}" \
    || fail "Annotated output does not contain atom_site data"

ok "PDB -> annotated mmCIF calculation works"
ok "Embedded mrc/mmCIF resources are usable"

echo "[INFO] Annotated mmCIF output: $(wc -l < "${MMCIF_OUTPUT}") lines"

# ----------------------------------------------------------------------
# 7. Exercise mcfp option parsing with --output-format
#
# This directly exercises a real command-line option in addition to
# --help/--version.
# ----------------------------------------------------------------------

DSSP_OUTPUT="${TMPDIR_DSSP}/test.dssp"

"${MKDSSP}" \
    --output-format=dssp \
    "${INPUT_PDB}" \
    "${DSSP_OUTPUT}"

[[ -s "${DSSP_OUTPUT}" ]] \
    || fail "Legacy DSSP output was not created"

grep -Eq 'RESIDUE[[:space:]]+AA[[:space:]]+STRUCTURE' "${DSSP_OUTPUT}" \
    || fail "Legacy DSSP residue header not found"

ok "--output-format=dssp works through mcfp integration"

# ----------------------------------------------------------------------
# 8. Verify that residues were actually processed
# ----------------------------------------------------------------------

RESIDUE_COUNT="$(
    awk '
        /RESIDUE[[:space:]]+AA[[:space:]]+STRUCTURE/ {
            in_residues = 1
            next
        }

        in_residues && length($0) > 10 {
            count++
        }

        END {
            print count + 0
        }
    ' "${DSSP_OUTPUT}"
)"

echo "[INFO] DSSP residue records: ${RESIDUE_COUNT}"

[[ "${RESIDUE_COUNT}" -ge 5 ]] \
    || fail "Expected at least 5 DSSP residue records, got ${RESIDUE_COUNT}"

ok "DSSP processed the synthetic protein residues"

# ----------------------------------------------------------------------
# 9. Show a small amount of output for inspection
# ----------------------------------------------------------------------

echo
echo "--- Legacy DSSP output header ---"
head -n 10 "${DSSP_OUTPUT}"

echo
echo "=== PASS: DSSP ${EXPECTED_VERSION} installation looks functional ==="
echo "[OK] Correct DSSP version"
echo "[OK] Patched mcfp command-line integration works"
echo "[OK] Runtime libraries resolve"
echo "[OK] PDB parsing works"
echo "[OK] Embedded mrc resources are usable"
echo "[OK] Annotated mmCIF generation works"
echo "[OK] Legacy DSSP generation works"