#!/usr/bin/env bash
set -euo pipefail

: "${EBROOTVCF2DIS:?EBROOTVCF2DIS not set; load the module first}"

need(){ command -v "$1" >/dev/null || { echo "ERROR: missing '$1' in PATH"; exit 2; }; }
need VCF2Dis
need VCF2Dis_single
need percentageboostrapTree.pl

srcroot="$EBROOTVCF2DIS/share/VCF2Dis"
[[ -d "$srcroot/RunTest" && -d "$srcroot/example" ]] || { echo "ERROR: expected $srcroot/{RunTest,example}"; exit 3; }

TIME_CMD="time -p"
for t in /bin/time /usr/bin/time; do
  [[ -x "$t" ]] || continue
  if "$t" -v true >/dev/null 2>&1; then TIME_CMD="$t -v -p"; break; fi
done

tmp="$(mktemp -d)"; trap 'echo "Workdir: '"$tmp"'" >&2; rm -rf "$tmp"' EXIT
cp -a "$srcroot/RunTest" "$tmp/"
cp -a "$srcroot/example" "$tmp/"
cd "$tmp/RunTest"

echo "== Workdir: $tmp"
echo "== TIME_CMD: $TIME_CMD"
echo

# Patch hardcoded old paths + /bin/time usage inside copied RunTest
find . -maxdepth 3 -type f -name '*.sh' -print0 | xargs -0 sed -i \
  -e 's#../VCF2Dis-1\.53/bin/VCF2Dis_single#VCF2Dis_single#g' \
  -e 's#../VCF2Dis-1\.53/bin/VCF2Dis_multi#VCF2Dis_multi#g' \
  -e 's#../VCF2Dis-1\.53/bin/VCF2Dis#VCF2Dis#g' \
  -e 's#/bin/time -v -p#'"$TIME_CMD"'#g'

# -----------------------
# Always-run “lite” tests
# -----------------------
echo "== 04.SupFigRun (VCF2Dis-only) =="
pushd 04.SupFigRun >/dev/null
cp -a ../../example/Example1/Khuman.vcf.gz ./
VCF2Dis_single -InPut Khuman.vcf.gz -OutPut p_dis.mat -InSampleGroup pop.info
test -s p_dis.mat
echo "OK: 04.SupFigRun p_dis.mat"
popd >/dev/null
echo

echo "== 05.pMat_Test (VCF2Dis-only) =="
pushd 05.pMat_Test >/dev/null
cp -a ../../example/Example1/Khuman.vcf.gz ./
VCF2Dis_single -InPut Khuman.vcf.gz -OutPut vcf2dis.mat -NoOUTtree >/dev/null
test -s vcf2dis.mat
echo "OK: 05.pMat_Test vcf2dis.mat (head)"
cut -f 1-5 vcf2dis.mat | head -n 6
popd >/dev/null
echo

echo "== Perl helper check =="
if command -v perl >/dev/null; then
  cat > merge.tre <<'TRE'
(A:1,B:2,C:3);
TRE
  perl "$(command -v percentageboostrapTree.pl)" merge.tre 10 boostrap.tre
  test -s boostrap.tre
  echo "OK: percentageboostrapTree.pl"
else
  echo "NOTE: perl not found; skipping"
fi
echo

# ---------------------------------------
# Optional 01/02 generation + VCF2Dis runs
# ---------------------------------------
if [[ "${RUN_BENCH:-0}" == "1" ]]; then
  : "${INVCF:?Set INVCF=/path/to/ALL.chr1....vcf.gz (1000G) to generate 01/02 inputs}"
  [[ -f "$INVCF" ]] || { echo "ERROR: INVCF not found: $INVCF"; exit 4; }

  echo "== 00.GetData: generating 01/02 inputs from INVCF =="
  pushd 00.GetData >/dev/null
  ln -sf "$INVCF" ALL.chr1.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
  bash step2_newSite.sh
  bash step3_newSample.sh
  popd >/dev/null
  echo "OK: generated M*.vcf.gz and 02.S*.vcf.gz"
  echo

  echo "== 01.TestBySite (VCF2Dis-only) =="
  pushd 01.TestBySite >/dev/null
  bash RunA.sh
  bash RunB.sh
  ls -lh p_dis.mat >/dev/null 2>&1 && echo "OK: 01.TestBySite produced p_dis.mat (last run)"
  popd >/dev/null
  echo

  echo "== 02.TestBySample (VCF2Dis-only) =="
  pushd 02.TestBySample >/dev/null
  bash RunA.sh
  bash RunB.sh
  ls -lh p_dis.mat >/dev/null 2>&1 && echo "OK: 02.TestBySample produced p_dis.mat (last run)"
  popd >/dev/null
  echo

  echo "NOTE: RunC/RunD (fastreeR/ngsDist) are benchmarking vs other tools and are not run here."
else
  echo "NOTE: skipping 01/02 generation+bench. To enable:"
  echo "  RUN_BENCH=1 INVCF=/path/to/ALL.chr1....vcf.gz bash $0"
fi

echo
echo "ALL OK"