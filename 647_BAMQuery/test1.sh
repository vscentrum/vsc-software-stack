#!/usr/bin/env bash
set -euo pipefail

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

export BAMQUERY_LIB="${BAMQUERY_LIB:-$HOME/BamQuery/lib}"
mkdir -p "$BAMQUERY_LIB"/genome_versions "$BAMQUERY_LIB"/snps

echo "[1] bamquery wrapper / argparse"
bamquery --help >/dev/null

echo "[2] Python dependencies"
python - <<'PY'
import tempfile
from pathlib import Path

import pandas as pd
import pysam
from Bio.Seq import Seq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import dill
import multiprocess
from pathos.pools import ProcessPool

tmp = Path(tempfile.mkdtemp())

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
xlsx = tmp / "test.xlsx"
df.to_excel(xlsx, index=False, engine="xlsxwriter")
df2 = pd.read_excel(xlsx, engine="openpyxl")
assert df2.equals(df)

assert str(Seq("ATGGCC").translate()) == "MA"

ax = sns.heatmap(df)
ax.figure.savefig(tmp / "heatmap.png")
plt.close(ax.figure)
assert (tmp / "heatmap.png").stat().st_size > 0

bam = tmp / "empty.bam"
header = {"HD": {"VN": "1.6"}, "SQ": [{"SN": "chr1", "LN": 100}]}
with pysam.AlignmentFile(str(bam), "wb", header=header):
    pass
pysam.index(str(bam))
with pysam.AlignmentFile(str(bam), "rb") as fh:
    assert fh.references == ("chr1",)

f = lambda x: x + 1
assert dill.loads(dill.dumps(f))(1) == 2

with multiprocess.Pool(2) as pool:
    assert pool.map(f, [1, 2, 3]) == [2, 3, 4]

pp = ProcessPool(nodes=2)
try:
    assert pp.map(abs, [-1, -2]) == [1, 2]
finally:
    pp.close()
    pp.join()
    pp.clear()

print("Python smoke test OK")
PY

echo "[3] R dependencies"
R -q --vanilla -e 'suppressPackageStartupMessages({library(ggplot2); library(data.table)}); f <- tempfile(fileext=".png"); dt <- data.table(x=1:3,y=3:1); p <- ggplot(dt, aes(x,y)) + geom_point(); ggsave(f, p, width=3, height=3); stopifnot(file.exists(f), file.info(f)$size > 0); cat("R smoke test OK\n")'

echo "[4] BEDTools"
printf "chr1\t10\t20\n" > "$tmpdir/a.bed"
printf "chr1\t15\t25\n" > "$tmpdir/b.bed"
bedtools intersect -a "$tmpdir/a.bed" -b "$tmpdir/b.bed" > "$tmpdir/out.bed"
grep -qx $'chr1\t15\t20' "$tmpdir/out.bed"

echo "[5] STAR basic functionality"
cat > "$tmpdir/ref.fa" <<'EOF'
>chr1
ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT
EOF

STAR \
  --runMode genomeGenerate \
  --runThreadN 1 \
  --genomeDir "$tmpdir/star_index" \
  --genomeFastaFiles "$tmpdir/ref.fa" \
  --genomeSAindexNbases 3 \
  >/dev/null 2>&1

cat > "$tmpdir/read.fq" <<'EOF'
@r1
ACGTACGTACGTACGT
+
FFFFFFFFFFFFFFFF
EOF

STAR \
  --runThreadN 1 \
  --genomeDir "$tmpdir/star_index" \
  --readFilesIn "$tmpdir/read.fq" \
  --outFileNamePrefix "$tmpdir/star_run/" \
  --outSAMtype BAM Unsorted \
  >/dev/null 2>&1

test -s "$tmpdir/star_run/Aligned.out.bam"

echo "[6] optional: verify patched BAMQUERY_LIB error"
unset BAMQUERY_LIB
if bamquery --help >"$tmpdir/noenv.out" 2>"$tmpdir/noenv.err"; then
  echo "ERROR: bamquery unexpectedly worked without BAMQUERY_LIB" >&2
  exit 1
fi
grep -q 'You have to set BAMQUERY_LIB' "$tmpdir/noenv.err"

echo "All pre-data BamQuery smoke tests passed"