#!/usr/bin/env bash
set -euo pipefail

genome="${1:-v38_104}"     # v26_88 | v33_99 | v38_104 | M24 | M30
dbsnp="${2:-}"             # optional: 149 | 151 | 155

export BAMQUERY_LIB="${BAMQUERY_LIB:-/data/gent/vo/001/gvo00117/vsc47063/BamQuery/lib}"

tmpdir=""

cleanup() {
  rc=$?
  if [[ -n "${tmpdir:-}" && -d "${tmpdir:-}" ]]; then
    if [[ $rc -eq 0 ]]; then
      rm -rf "$tmpdir"
    else
      echo "[INFO] Keeping temporary directory for inspection: $tmpdir" >&2
    fi
  fi
}
trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "[INFO] $*"
}

require_file() {
  test -f "$1" || fail "Missing file: $1"
}

require_dir() {
  test -d "$1" || fail "Missing directory: $1"
}

case "$genome" in
  v26_88) genome_subdir="genome_v26_88/Index_STAR_2.7.9a" ;;
  v33_99) genome_subdir="genome_v33_99/Index_STAR_2.7.9a" ;;
  v38_104) genome_subdir="genome_v38_104/Index_STAR_2.7.9a" ;;
  M24) genome_subdir="genome_mouse_m24/Index_STAR_2.7.9a" ;;
  M30) genome_subdir="genome_mouse_m30/Index_STAR_2.7.9a" ;;
  *) fail "Unsupported genome '$genome'" ;;
esac

STAR_INDEX="$BAMQUERY_LIB/genome_versions/$genome_subdir"

info "Using BAMQUERY_LIB=$BAMQUERY_LIB"

info "Checking bamquery wrapper and BAMQUERY_LIB"
command -v bamquery >/dev/null || fail "bamquery not found in PATH"
require_dir "$BAMQUERY_LIB"
require_dir "$BAMQUERY_LIB/genome_versions"
require_dir "$BAMQUERY_LIB/snps"

info "Checking expected BamQuery data files"
require_file "$BAMQUERY_LIB/README.txt"
require_dir "$STAR_INDEX"
require_file "$STAR_INDEX/chrName.txt"
require_file "$STAR_INDEX/sjdbList.fromGTF.out.tab"
require_file "$STAR_INDEX/Genome"
require_file "$STAR_INDEX/SA"
require_file "$STAR_INDEX/SAindex"

if [[ -n "$dbsnp" ]]; then
  info "Checking dbSNP payload presence for release $dbsnp"
  find "$BAMQUERY_LIB/snps" -maxdepth 3 -type f | grep -q "$dbsnp" || \
    fail "Did not find any dbSNP files matching release $dbsnp under $BAMQUERY_LIB/snps"
fi

# info "Checking bamquery help"
# bamquery --help >/dev/null

info "STAR version: $(STAR --version)"

tmpdir=$(mktemp -d)

info "Running STAR against BamQuery index to validate index compatibility"
cat > "$tmpdir/read.fq" <<'EOF'
@r1
ACGTACGTACGTACGTACGTACGTACGTACGT
+
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
EOF

mkdir -p "$tmpdir/star_run"
if STAR \
  --runThreadN 1 \
  --genomeDir "$STAR_INDEX" \
  --readFilesIn "$tmpdir/read.fq" \
  --outFileNamePrefix "$tmpdir/star_run/" \
  --outSAMtype None \
  >/dev/null 2>&1
then
  :
else
  star_ec=$?
  if grep -q "Started loading the genome" "$tmpdir/star_run/Log.out" 2>/dev/null; then
    echo "STAR started reading the BamQuery index, so this is not an obvious index-version mismatch." >&2
    echo "The process likely ran out of memory while loading the genome/SA/SAindex." >&2
  fi
  echo >&2
  echo "Last lines of Log.out:" >&2
  tail -n 50 "$tmpdir/star_run/Log.out" 2>/dev/null >&2 || true
  echo >&2
  echo "Last lines of Log.final.out:" >&2
  tail -n 50 "$tmpdir/star_run/Log.final.out" 2>/dev/null >&2 || true
  exit "$star_ec"
fi

require_file "$tmpdir/star_run/Log.out"
require_file "$tmpdir/star_run/Log.final.out"

if ! grep -q "Finished on" "$tmpdir/star_run/Log.final.out"; then
  echo "Last lines of Log.out:" >&2
  tail -n 50 "$tmpdir/star_run/Log.out" >&2 || true
  echo >&2
  echo "Last lines of Log.final.out:" >&2
  tail -n 50 "$tmpdir/star_run/Log.final.out" >&2 || true
  fail "STAR exited successfully but Log.final.out does not contain a completion marker"
fi

info "STAR index compatibility test passed"

info "Checking Python-side runtime pieces still import"
python - <<'PY'
import os
import pandas, pysam, matplotlib, seaborn, xlsxwriter, openpyxl, Bio, dill, multiprocess, pathos
print("Python runtime imports OK")
print("BAMQUERY_LIB =", os.environ["BAMQUERY_LIB"])
PY

info "All BamQuery post-download validation checks passed"