#!/bin/bash
set -euo pipefail

need(){ command -v "$1" >/dev/null || { echo "ERROR: missing '$1' in PATH"; exit 2; }; }

need VCF2Dis
need VCF2Dis_single
need VCF2Dis_multi
need percentageboostrapTree.pl

echo "VCF2Dis:              $(command -v VCF2Dis)"
echo "VCF2Dis_single:       $(command -v VCF2Dis_single)"
echo "VCF2Dis_multi:        $(command -v VCF2Dis_multi)"
echo "percentageboostrapTree.pl: $(command -v percentageboostrapTree.pl)"
echo

echo "== libz resolution =="
ldd "$(command -v VCF2Dis)" | grep -E 'libz\.so|zlib' || true
echo

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cd "$tmp"

cat > toy.vcf <<'VCF'
##fileformat=VCFv4.2
##contig=<ID=1,length=1000>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT S1 S2 S3 S4
1 1 . A C . PASS . GT 0/0 0/1 1/1 0/1
1 2 . A C . PASS . GT 0/0 0/1 1/1 0/1
1 3 . A C . PASS . GT 0/0 0/1 1/1 0/1
1 4 . A C . PASS . GT 0/0 0/1 1/1 0/1
VCF
tr -s ' ' '\t' < toy.vcf > toy.vcf.tmp && mv toy.vcf.tmp toy.vcf
gzip -c toy.vcf > toy.vcf.gz

VCF2Dis -InPut toy.vcf    -OutPut toy.mat
VCF2Dis -InPut toy.vcf.gz -OutPut toy_gz.mat

py="$(command -v python3 || command -v python || true)"
if [[ -n "$py" ]]; then
  "$py" - <<'PY'
def read(fn):
  ls=[l.strip() for l in open(fn) if l.strip()]
  n=int(ls[0].split()[0])
  names=[]; mat=[]
  for l in ls[1:1+n]:
    p=l.split()
    names.append(p[0])
    mat.append([float(x) for x in p[1:1+n+1]])
  return names,mat
def chk(names,mat):
  assert names==["S1","S2","S3","S4"],names
  exp=[
    [0.0,0.5,1.0,0.5],
    [0.5,0.0,0.5,0.0],
    [1.0,0.5,0.0,0.5],
    [0.5,0.0,0.5,0.0],
  ]
  for i in range(4):
    for j in range(4):
      assert abs(mat[i][j]-mat[j][i])<1e-9,(i,j,mat[i][j],mat[j][i])
      assert abs(mat[i][j]-exp[i][j])<1e-6,(i,j,mat[i][j],exp[i][j])
for fn in ["toy.mat","toy_gz.mat"]:
  n,m=read(fn); chk(n,m)
print("OK: matrix matches expected values (4-sample toy)")
PY
else
  echo "WARN: python not found; skipping numeric checks"
fi

printf "S1\nS2\nS3\n" > subpop.list
VCF2Dis -InPut toy.vcf -OutPut sub.mat -SubPop subpop.list
if [[ -n "$py" ]]; then
  "$py" - <<'PY'
ls=[l.strip() for l in open("sub.mat") if l.strip()]
assert ls[0].split()[0]=="3",ls[0]
names=[ls[i].split()[0] for i in (1,2,3)]
assert names==["S1","S2","S3"],names
print("OK: -SubPop produced 3x3 matrix with expected samples")
PY
fi

VCF2Dis_single -InPut toy.vcf -OutPut single.mat
VCF2Dis_multi  -InPut toy.vcf -OutPut multi.mat
if [[ -n "$py" ]]; then
  "$py" - <<'PY'
def mat(fn):
  ls=[l.strip() for l in open(fn) if l.strip()]
  n=int(ls[0].split()[0])
  return [[float(x) for x in ls[i].split()[1:1+n+1]] for i in range(1,1+n)]
a=mat("toy.mat"); b=mat("single.mat"); c=mat("multi.mat")
for x in (b,c):
  for i in range(len(a)):
    for j in range(len(a)):
      assert abs(a[i][j]-x[i][j])<1e-9,(i,j,a[i][j],x[i][j])
print("OK: VCF2Dis/_single/_multi consistent")
PY
fi

if command -v perl >/dev/null; then
  cat > merge.tre <<'TRE'
(S1:80,S2:50,S3:100,S4:50);
TRE
  perl "$(command -v percentageboostrapTree.pl)" merge.tre 10 boostrap.tre
  [[ -s boostrap.tre ]] && echo "OK: percentageboostrapTree.pl ran via perl" || { echo "FAIL: perl helper produced no output"; exit 3; }
else
  echo "NOTE: perl not found; skipping percentageboostrapTree.pl check"
fi

if command -v Rscript >/dev/null; then
  Rscript -e 'ok=all(sapply(c("ape","ggtree"), function(p) requireNamespace(p, quietly=TRUE))); if(!ok){cat("FAIL: missing R pkgs: ape/ggtree\n"); q(status=4)}; cat("OK: R pkgs ape+ggtree available\n")'
else
  echo "NOTE: Rscript not found; skipping R checks"
fi

echo "ALL OK (workdir was: $tmp)"