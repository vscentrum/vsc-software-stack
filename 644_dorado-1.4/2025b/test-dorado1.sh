#!/bin/bash
set -euo pipefail

EXPECTED_VERSION="2.1.2"
MODEL="dna_r10.4.1_e8.2_400bps_hac@v6.0.0"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

pass() {
    echo "PASS: $*"
}

echo "=== Dorado smoke test ==="

command -v dorado >/dev/null 2>&1 || fail "dorado is not in PATH"
DORADO=$(command -v dorado)
echo "Dorado: $DORADO"

VERSION_OUTPUT=$(dorado --version 2>&1)
echo "Version: $VERSION_OUTPUT"
echo "$VERSION_OUTPUT" | grep -F "$EXPECTED_VERSION" >/dev/null ||
    fail "expected Dorado $EXPECTED_VERSION"
pass "Dorado version"

for cmd in basecaller aligner demux download duplex summary trim; do
    dorado "$cmd" --help >/dev/null 2>&1 || fail "'dorado $cmd --help' failed"
done
pass "core subcommands"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

dorado download --list-yaml > "$tmpdir/models.yaml"
grep -F -- "$MODEL" "$tmpdir/models.yaml" >/dev/null ||
    fail "$MODEL is not present in the model catalogue"
pass "model catalogue"

mkdir -p "$tmpdir/models"
dorado download --model "$MODEL" --models-directory "$tmpdir/models"

MODEL_DIR="$tmpdir/models/$MODEL"
test -d "$MODEL_DIR" || fail "downloaded model directory was not created"
test -n "$(find "$MODEL_DIR" -type f -print -quit)" ||
    fail "downloaded model directory is empty"
pass "model download"

if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi >/dev/null || fail "nvidia-smi failed"
    pass "NVIDIA GPU/driver visibility"
else
    echo "WARNING: nvidia-smi is not available; skipping direct GPU driver check"
fi

if [ "$#" -eq 0 ]; then
    echo
    echo "Basic installation checks passed."
    echo "For a real CUDA basecalling test, run:"
    echo "  $0 /path/to/test.pod5"
    echo "or:"
    echo "  $0 /path/to/pod5_directory"
    exit 0
fi

INPUT=$1
test -e "$INPUT" || fail "POD5 input does not exist: $INPUT"

echo
echo "Running real CUDA basecalling test..."
dorado basecaller \
    "$MODEL_DIR" \
    "$INPUT" \
    --device cuda:0 \
    > "$tmpdir/calls.bam"

test -s "$tmpdir/calls.bam" || fail "basecaller produced an empty BAM"

dorado summary "$tmpdir/calls.bam" > "$tmpdir/summary.tsv"
test -s "$tmpdir/summary.tsv" || fail "dorado summary produced no output"

READS=$(tail -n +2 "$tmpdir/summary.tsv" | wc -l)
test "$READS" -gt 0 || fail "no reads were present in the basecaller output"

pass "CUDA basecalling"
pass "BAM parsing with dorado summary"

if command -v samtools >/dev/null 2>&1; then
    samtools quickcheck "$tmpdir/calls.bam" ||
        fail "samtools quickcheck rejected the generated BAM"
    pass "BAM validation with samtools"
fi

echo
echo "Dorado smoke test PASSED"
echo "Basecalled reads: $READS"