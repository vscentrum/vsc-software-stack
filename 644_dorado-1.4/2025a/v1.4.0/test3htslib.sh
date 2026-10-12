#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] dorado: $(command -v dorado)"

echo "[TEST] top-level and aligner help"
dorado -h >/dev/null
dorado aligner -h >/dev/null

echo "[TEST] linkage to HTSlib"
ldd "$(command -v dorado)" | grep -i hts || true

cat > ref.fa <<'EOF'
>chr1
ACGTACGTACGTACGTACGTACGTACGTACGT
EOF

cat > reads.fq <<'EOF'
@read1
ACGTACGTACGTACGT
+
IIIIIIIIIIIIIIII
EOF

echo "[TEST] align tiny FASTQ -> BAM"
dorado aligner ref.fa reads.fq > aln.bam

test -s aln.bam

echo "[TEST] align tiny FASTQ -> SAM for inspection"
dorado aligner ref.fa reads.fq --emit-sam > aln.sam

test -s aln.sam

echo "[INFO] first lines of SAM:"
head -n 20 aln.sam

echo "[OK] Dorado HTS I/O smoke test passed"