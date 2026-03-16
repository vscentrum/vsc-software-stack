#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <pod5_file_or_dir> <outdir> [model]"
    exit 1
fi

INPUT="$1"
OUTDIR="$2"
MODEL="${3:-hac}"

mkdir -p "$OUTDIR"

BAM="$OUTDIR/calls.bam"
TSV="$OUTDIR/summary.tsv"
LOG="$OUTDIR/dorado.log"

echo "[INFO] input : $INPUT"
echo "[INFO] outdir: $OUTDIR"
echo "[INFO] model : $MODEL"

echo "[RUN] basecalling"
dorado basecaller "$MODEL" "$INPUT" >"$BAM" 2>"$LOG"

test -s "$BAM"

echo "[RUN] summary"
dorado summary "$BAM" >"$TSV"

test -s "$TSV"

echo "[INFO] first lines of summary:"
head -n 5 "$TSV" || true

echo "[OK] Tiny Dorado run finished"
echo "[OK] BAM: $BAM"
echo "[OK] TSV: $TSV"
echo "[OK] LOG: $LOG"