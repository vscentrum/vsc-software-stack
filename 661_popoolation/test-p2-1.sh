#!/bin/bash
set -euo pipefail

root=${EBROOTPOPOOLATION2:?Load the PoPoolation2 module before running this test}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

pass() {
    echo "PASS: $*"
}

run_logged() {
    local label=$1
    shift
    local logfile="$tmpdir/${label//[^A-Za-z0-9_.-]/_}.log"

    if "$@" >"$logfile" 2>&1; then
        pass "$label"
    else
        cat "$logfile" >&2
        fail "$label"
    fi
}

[[ -d "$root" ]] || fail "installation directory does not exist: $root"
[[ ${EBVERSIONPOPOOLATION2:-} == 1201 ]] || \
    fail "unexpected PoPoolation2 version: ${EBVERSIONPOPOOLATION2:-unset}"

for cmd in perl Rscript java; do
    command -v "$cmd" >/dev/null || fail "$cmd is not available"
done

expected_files=(
    cmh-test.pl
    create-genewise-sync.pl
    fisher-test.pl
    fst-sliding.pl
    mpileup2sync.jar
    mpileup2sync.pl
    snp-frequency-diff.pl
    subsample-synchronized.pl
    synchronize-pileup.pl
)

expected_dirs=(
    Modules
    export
    indel_filtering
)

for path in "${expected_files[@]}"; do
    [[ -f "$root/$path" ]] || fail "missing file: $path"
done

for path in "${expected_dirs[@]}"; do
    [[ -d "$root/$path" ]] || fail "missing directory: $path"
done

[[ ! -e "$root/popoolation2_1201" ]] || fail "unflattened popoolation2_1201 directory remains"
[[ ! -e "$root/TextNSP" ]] || fail "TextNSP build directory remains"

if [[ -e "$root/.svn" ]]; then
    echo "WARNING: obsolete .svn metadata is installed"
else
    pass "no top-level .svn metadata"
fi

pass "installation layout"

text_nsp_path=$(
    perl -MText::NSP::Measures::2D::Fisher::twotailed \
        -e 'print $INC{"Text/NSP/Measures/2D/Fisher/twotailed.pm"}'
)

[[ -n "$text_nsp_path" ]] || fail "could not resolve Text::NSP Fisher module"
case "$text_nsp_path" in
    "$root"/*)
        pass "Text::NSP resolves from PoPoolation2 installation"
        ;;
    *)
        fail "Text::NSP resolves outside PoPoolation2: $text_nsp_path"
        ;;
esac

case ":${PERL5LIB:-}:" in
    *":$root/lib/perl5/site_perl/"*)
        pass "PoPoolation2 Perl library path is present in PERL5LIB"
        ;;
    *)
        fail "PoPoolation2 Perl library path is missing from PERL5LIB"
        ;;
esac

mapfile -d '' perl_scripts < <(
    find "$root" -type f -name '*.pl' -print0 | sort -z
)

((${#perl_scripts[@]} > 0)) || fail "no Perl scripts found"

for script in "${perl_scripts[@]}"; do
    rel=${script#"$root"/}
    run_logged "syntax $rel" \
        bash -c 'cd "$1" && perl -c "$2"' _ "$tmpdir" "$script"
done

mapfile -d '' perl_modules < <(
    find "$root/Modules" -type f -name '*.pm' \
        ! -path "$root/Modules/Test/TCMH.pm" -print0 | sort -z
)

((${#perl_modules[@]} > 0)) || fail "no bundled Perl modules found"

for module in "${perl_modules[@]}"; do
    rel=${module#"$root"/}
    run_logged "syntax $rel" \
        bash -c 'cd "$1" && perl -I"$2/Modules" -c "$3"' \
        _ "$tmpdir" "$root" "$module"
done

run_logged "mpileup2sync embedded tests" \
    bash -c 'cd "$1" && perl "$2/mpileup2sync.pl" --test' \
    _ "$tmpdir" "$root"

fisher_log="$tmpdir/fisher-test.log"
if bash -c 'cd "$1" && perl "$2/fisher-test.pl" --test' \
    _ "$tmpdir" "$root" >"$fisher_log" 2>&1; then
    if grep -Eq 'unrecognised method|Use of uninitialized value .*winSumMethod' "$fisher_log"; then
        cat "$fisher_log" >&2
        fail "fisher-test completed with the stale window-summary test bug"
    fi
    pass "fisher-test embedded tests"
else
    cat "$fisher_log" >&2
    fail "fisher-test embedded tests"
fi

run_logged "fst-sliding embedded tests" \
    bash -c 'cd "$1" && perl "$2/fst-sliding.pl" --test' \
    _ "$tmpdir" "$root"

run_logged "cmh-test embedded tests" \
    bash -c 'cd "$1" && perl "$2/cmh-test.pl" --test' \
    _ "$tmpdir" "$root"

run_logged "R runtime" \
    Rscript -e 'stopifnot(getRversion() >= package_version("2.7.0"))'

java_log="$tmpdir/mpileup2sync-java.log"
set +e
java -jar "$root/mpileup2sync.jar" --help >"$java_log" 2>&1
java_rc=$?
set -e

if grep -Eq \
    'Exception|Error: Could not find|UnsupportedClassVersionError|NoClassDefFoundError' \
    "$java_log"; then
    cat "$java_log" >&2
    fail "mpileup2sync.jar could not start"
fi

if [[ $java_rc -le 1 ]] && grep -Eqi 'usage|mpileup2sync|input|output' "$java_log"; then
    pass "mpileup2sync.jar starts under Java"
else
    cat "$java_log" >&2
    fail "unexpected mpileup2sync.jar --help result, exit code $java_rc"
fi

case ":$PATH:" in
    *":$root:"*)
        echo "NOTE: PoPoolation2 root is in PATH, but the tests did not rely on it"
        ;;
    *)
        pass "no PoPoolation2 PATH entry required"
        ;;
esac

printf '\nAll PoPoolation2 smoke tests passed.\n'