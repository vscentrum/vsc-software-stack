#!/usr/bin/env bash
set -Eeuo pipefail

WORKDIR="${WORKDIR:-$(mktemp -d "${TMPDIR:-/tmp}/psn-smoke.XXXXXX")}"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

run() {
    echo "+ $*"
    "$@"
}

echo "== PsN smoke test =="
echo "workdir: ${WORKDIR}"

export R_LIBS_USER=
export R_PROFILE_USER=/dev/null
export R_ENVIRON_USER=/dev/null

echo
echo "== Environment =="
echo "PATH=$PATH"
echo "PERL5LIB=${PERL5LIB:-<unset>}"
echo "R_LIBS_SITE=${R_LIBS_SITE:-<unset>}"
echo "EBROOTPSN=${EBROOTPSN:-<unset>}"
echo "EBROOTPSNR=${EBROOTPSNR:-<unset>}"
echo "EBROOTNONMEM=${EBROOTNONMEM:-<unset>}"

echo
echo "== Required commands =="
for cmd in perl Rscript execute psn qa nmfe76; do
    command -v "$cmd" >/dev/null 2>&1 || fail "missing command: $cmd; load the required module(s) first"
    echo "$cmd -> $(command -v "$cmd")"
done

echo
echo "== Basic CLI checks =="
run execute -h >/dev/null
run psn -h >/dev/null
run qa -h >/dev/null

echo
echo "== PsNR check =="
Rscript --vanilla -e 'library(PsNR); cat("PsNR", as.character(packageVersion("PsNR")), "OK\n")'

echo
echo "== Perl module dependency check =="
perl -MStatistics::Distributions -MFile::Copy::Recursive -MFile::HomeDir -MMath::SigFigs -MCapture::Tiny -MMath::Random::Free -MMath::MatrixReal -MMouse -MMouseX::Params::Validate -MYAML -MArchive::Zip -e 'print "Perl dependencies OK\n"'

echo
echo "== PsN installation layout =="
test -n "${EBROOTPSN:-}" || fail "EBROOTPSN is not set"
test -x "$EBROOTPSN/bin/execute" || fail "$EBROOTPSN/bin/execute missing or not executable"
test -x "$EBROOTPSN/bin/psn" || fail "$EBROOTPSN/bin/psn missing or not executable"
test -x "$EBROOTPSN/bin/qa" || fail "$EBROOTPSN/bin/qa missing or not executable"

PSN_CONF="$(find "$EBROOTPSN" -path '*PsN_5_6_0/psn.conf' -print -quit)"
test -n "$PSN_CONF" || fail "psn.conf not found under EBROOTPSN"
echo "psn.conf -> $PSN_CONF"
grep -q '^default=nmfe76,7.6' "$PSN_CONF" || fail "default nmfe76 entry not found in psn.conf"
grep -q '^nm760=nmfe76,7.6' "$PSN_CONF" || fail "nm760 entry not found in psn.conf"

echo
echo "== Creating tiny NONMEM/PsN test case =="
mkdir -p "$WORKDIR"
cd "$WORKDIR"

cat > psn_smoke.csv <<'EOF'
@ID TIME DV
1 0 5.0
1 1 5.2
1 2 4.8
2 0 7.0
2 1 6.9
2 2 7.1
EOF

cat > psn_smoke.mod <<'EOF'
$PROBLEM PsN NONMEM smoke test: simple PRED simulation

$INPUT ID TIME DV
$DATA psn_smoke.csv IGNORE=@

$PRED
IPRED = THETA(1)
Y = IPRED + EPS(1)

$THETA
5

$SIGMA
1

$SIMULATION (123456) ONLYSIM

$TABLE ID TIME DV IPRED FILE=sdtab NOAPPEND NOPRINT
EOF

echo "test files:"
ls -l psn_smoke.csv psn_smoke.mod

echo
echo "== Running PsN execute =="
set +e
execute psn_smoke.mod -dir=psn_execute > execute.stdout 2> execute.stderr
status=$?
set -e

if [ "$status" -ne 0 ]; then
    echo "execute.stdout:"
    cat execute.stdout || true
    echo "execute.stderr:"
    cat execute.stderr || true
    fail "PsN execute returned non-zero exit status: $status"
fi

echo
echo "== PsN/NONMEM output files =="
find "$WORKDIR" -maxdepth 4 -type f | sort | sed "s#^$WORKDIR/##" | head -100

LST_FILE="$(find "$WORKDIR" -type f \( -name '*.lst' -o -name '*.lst.gz' \) -print -quit || true)"
FMSG_FILE="$(find "$WORKDIR" -type f -name 'FMSG' -print -quit || true)"
ERR_FILE="$(find "$WORKDIR" -type f -name 'psn_nonmem_error_messages.txt' -print -quit || true)"
SDTAB_FILE="$(find "$WORKDIR" -type f -name 'sdtab' -print -quit || true)"

test -n "$LST_FILE" || fail "no NONMEM .lst file found after PsN execute"
echo "lst file -> $LST_FILE"

if [ -n "$FMSG_FILE" ]; then
    echo "FMSG file -> $FMSG_FILE"
fi

if [ -n "$ERR_FILE" ] && [ -s "$ERR_FILE" ]; then
    echo
    echo "psn_nonmem_error_messages.txt is non-empty:"
    cat "$ERR_FILE"
    fail "NONMEM/PsN reported errors"
fi

echo
echo "== Checking for actual NONMEM failure markers =="
CHECK_FILES=(execute.stderr execute.stdout)
[ -n "$FMSG_FILE" ] && CHECK_FILES+=("$FMSG_FILE")
[ -n "$LST_FILE" ] && CHECK_FILES+=("$LST_FILE")

set +e
grep -HniE 'NMtran failed|run failed|AN ERROR WAS FOUND|ERROR IN|TERMINATED DUE|PROGRAM TERMINATED' "${CHECK_FILES[@]}"
grep_status=$?
set -e

if [ "$grep_status" -eq 0 ]; then
    fail "actual NONMEM/PsN failure markers detected"
fi

if [ -n "$SDTAB_FILE" ]; then
    echo
    echo "sdtab -> $SDTAB_FILE"
    head "$SDTAB_FILE" || true
else
    echo
    echo "warning: sdtab not found; execute completed and no failure markers were detected"
fi

RAW_RESULTS="$(find "$WORKDIR" -type f -name 'raw_results_*.csv' -print -quit || true)"
if [ -n "$RAW_RESULTS" ]; then
    echo
    echo "raw results -> $RAW_RESULTS"
    head "$RAW_RESULTS" || true
fi

echo
echo "== Success =="
echo "PsN command wrappers OK"
echo "PsNR runtime OK"
echo "NONMEM executable visible OK"
echo "PsN execute real model run OK"
echo "workdir retained at: $WORKDIR"