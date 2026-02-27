#!/usr/bin/env bash
set -euo pipefail

: "${EBROOTVCF2DIS:?EBROOTVCF2DIS not set; load the module first}"

need(){ command -v "$1" >/dev/null || { echo "ERROR: missing '$1' in PATH"; exit 2; }; }
need VCF2Dis
command -v Rscript >/dev/null || echo "NOTE: Rscript not in PATH; some checks will be skipped"
command -v perl    >/dev/null || echo "NOTE: perl not in PATH; perl helper check will be skipped"

root="${1:-$EBROOTVCF2DIS/share/VCF2Dis/RunTest}"
[[ -d "$root" ]] || { echo "ERROR: RunTest dir not found: $root"; exit 3; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
out="$tmp/out"; mkdir -p "$out"

echo "== RunTest root: $root"
echo "== Output dir:   $out"
echo

if [[ -f "$root/md5sum.txt" ]] && command -v md5sum >/dev/null; then
  echo "== md5sum check =="
  (cd "$root" && md5sum -c md5sum.txt) || echo "NOTE: md5sum check reported mismatches (review output above)"
  echo
fi

find_inputs(){
  local d="$1" maxd="${2:-2}"
  find "$d" -maxdepth "$maxd" -type f \( -name '*.vcf.gz' -o -name '*.vcf' -o -name '*.fa.gz' -o -name '*.fa' -o -name '*.fasta.gz' -o -name '*.fasta' -o -name '*.phy.gz' -o -name '*.phy' \) | sort
}

run_vcf2dis_dir(){
  local d="$1" tag="$2"
  mapfile -t ins < <(find_inputs "$d" 2)
  if (( ${#ins[@]} == 0 )); then
    echo "SKIP $tag: no VCF/FA/PHY inputs found"
    return 0
  fi
  mkdir -p "$out/$tag"
  pushd "$out/$tag" >/dev/null
  echo "== $tag =="
  printf "Inputs:\n"; printf "  %s\n" "${ins[@]}"

  local first="${ins[0]}"
  if [[ "$first" == *.fa || "$first" == *.fa.gz || "$first" == *.fasta || "$first" == *.fasta.gz ]]; then
    VCF2Dis -InPut "$first" -OutPut p_dis.mat -InFormat FA
  elif [[ "$first" == *.phy || "$first" == *.phy.gz ]]; then
    VCF2Dis -InPut "$first" -OutPut p_dis.mat -InFormat PHY
  else
    VCF2Dis -InPut "${ins[@]}" -OutPut p_dis.mat
  fi

  [[ -s p_dis.mat ]] || { echo "FAIL $tag: p_dis.mat not created"; exit 10; }
  [[ -s p_dis.nwk ]] && echo "OK $tag: p_dis.nwk" || echo "NOTE $tag: no p_dis.nwk"
  [[ -s p_dis.pdf ]] && echo "OK $tag: p_dis.pdf" || echo "NOTE $tag: no p_dis.pdf"
  echo
  popd >/dev/null
}

run_pmat_test(){
  local d="$1" tag="$2"
  mkdir -p "$out/$tag"
  pushd "$out/$tag" >/dev/null
  echo "== $tag =="

  local m
  m="$(find "$d" -maxdepth 2 -type f \( -name '*.mat' -o -name '*p_dis*' -o -name '*.pMat*' \) | head -n1 || true)"
  if [[ -z "$m" ]]; then
    echo "SKIP $tag: no candidate matrix file found"
    popd >/dev/null
    echo
    return 0
  fi
  echo "Using matrix: $m"
  cp -a "$m" ./p_dis.mat || true

  if command -v Rscript >/dev/null; then
    Rscript -e 'f="p_dis.mat"; x=readLines(f); if(length(x)<3) quit(status=5); m=read.table(f,header=F,row.names=1,skip=1); suppressPackageStartupMessages(library(ape)); tr=nj(as.dist(as.matrix(m))); write.tree(tr,file="p_dis_from_mat.nwk"); cat("OK: wrote p_dis_from_mat.nwk\n")'
    [[ -s p_dis_from_mat.nwk ]] || { echo "FAIL $tag: did not produce tree"; exit 11; }
  else
    echo "NOTE: Rscript not available; skipping NJ-from-matrix check"
  fi
  echo
  popd >/dev/null
}

# Core RunTest subsets
run_vcf2dis_dir "$root/01.TestBySite"   "01.TestBySite"
run_vcf2dis_dir "$root/02.TestBySample" "02.TestBySample"
run_pmat_test    "$root/05.pMat_Test"   "05.pMat_Test"

# Optional heavier/plotting workflows
if [[ "${RUN_FIGS:-0}" == "1" ]]; then
  run_vcf2dis_dir "$root/03.Fig1Run"   "03.Fig1Run"
  run_vcf2dis_dir "$root/04.SupFigRun" "04.SupFigRun"
else
  echo "NOTE: skipping 03.Fig1Run and 04.SupFigRun (set RUN_FIGS=1 to enable)"
  echo
fi

# Perl helper quick sanity (invoke explicitly via perl; shebang doesn’t matter)
if command -v perl >/dev/null; then
  echo "== Perl helper check =="
  cat > "$out/merge.tre" <<'TRE'
(A:1,B:2,C:3);
TRE
  perl "$(command -v percentageboostrapTree.pl)" "$out/merge.tre" 10 "$out/boostrap.tre"
  [[ -s "$out/boostrap.tre" ]] && echo "OK: percentageboostrapTree.pl ran" || { echo "FAIL: perl helper produced no output"; exit 12; }
  echo
fi

echo "DONE. Results were in: $out"