#!/usr/bin/env bash
set -euo pipefail

: "${EBROOTVCF2DIS:?EBROOTVCF2DIS not set; load the module first}"

need(){ command -v "$1" >/dev/null || { echo "ERROR: missing '$1' in PATH"; exit 2; }; }
need VCF2Dis

exroot="$EBROOTVCF2DIS/share/VCF2Dis/example"
[[ -d "$exroot" ]] || { echo "ERROR: example dir not found at $exroot"; exit 3; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
out="$tmp/out"; mkdir -p "$out"

pick_input(){
  local d="$1"
  local f
  f="$(ls -1 "$d"/*.vcf.gz "$d"/*.vcf 2>/dev/null | head -n1 || true)"
  [[ -n "$f" ]] && { echo "VCF:$f"; return; }
  f="$(ls -1 "$d"/*.fa.gz "$d"/*.fa "$d"/*.fasta.gz "$d"/*.fasta 2>/dev/null | head -n1 || true)"
  [[ -n "$f" ]] && { echo "FA:$f"; return; }
  f="$(ls -1 "$d"/*.phy.gz "$d"/*.phy 2>/dev/null | head -n1 || true)"
  [[ -n "$f" ]] && { echo "PHY:$f"; return; }
  echo ""
}

for d in "$exroot"/Example*; do
  [[ -d "$d" ]] || continue
  tag="$(basename "$d")"
  sel="$(pick_input "$d")"
  if [[ -z "$sel" ]]; then
    echo "SKIP $tag: no .vcf/.fa/.phy inputs found"
    continue
  fi
  kind="${sel%%:*}"; f="${sel#*:}"

  w="$out/$tag"; mkdir -p "$w"; cd "$w"
  echo "== $tag ($kind) =="

  if [[ "$kind" == "VCF" ]]; then
    VCF2Dis -InPut "$f" -OutPut p_dis.mat
  else
    VCF2Dis -InPut "$f" -OutPut p_dis.mat -InFormat "$kind"
  fi

  [[ -s p_dis.mat ]] || { echo "FAIL $tag: p_dis.mat not created"; exit 10; }
  echo "OK $tag: p_dis.mat"

  # optional outputs (may depend on R pkgs / plotting)
  [[ -s p_dis.nwk ]] && echo "OK $tag: p_dis.nwk" || echo "NOTE $tag: no p_dis.nwk"
  [[ -s p_dis.pdf ]] && echo "OK $tag: p_dis.pdf" || echo "NOTE $tag: no p_dis.pdf"
  echo
done

echo "DONE. Results in: $out"