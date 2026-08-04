#!/bin/bash
set -euo pipefail

root=${EBROOTPOPOOLATION:?Load the PoPoolation module before running this test}
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
[[ ${EBVERSIONPOPOOLATION:-} == 1.2.3 ]] || \
    fail "unexpected PoPoolation version: ${EBVERSIONPOPOOLATION:-unset}"

command -v perl >/dev/null || fail "Perl is not available"
command -v R >/dev/null || fail "R is not available"
command -v Rscript >/dev/null || fail "Rscript is not available"

expected_files=(
    Variance-at-position.pl
    Variance-for-feature.pl
    Variance-sliding.pl
    VarSliding2Flybase.pl
    VarSliding2Wiggle.pl
    Visualise-output.pl
    calculate-dxy.pl
    mauve-parser.pl
    basic-pipeline/trim-fastq.pl
)

expected_dirs=(
    Modules
    basic-pipeline
    syn-nonsyn
)

for path in "${expected_files[@]}"; do
    [[ -f "$root/$path" ]] || fail "missing file: $path"
done

for path in "${expected_dirs[@]}"; do
    [[ -d "$root/$path" ]] || fail "missing directory: $path"
done

[[ ! -e "$root/.svn" ]] || fail ".svn was not removed"
[[ ! -e "$root/debug" ]] || fail "debug was not removed"

pass "installation layout"

mapfile -d '' perl_scripts < <(
    find "$root" -type f -name '*.pl' -print0 | sort -z
)

((${#perl_scripts[@]} > 0)) || fail "no Perl scripts found"

for script in "${perl_scripts[@]}"; do
    rel=${script#"$root"/}
    run_logged "syntax $rel" env -u PERL5LIB perl -c "$script"
done

mapfile -d '' perl_modules < <(
    find "$root/Modules" -type f -name '*.pm' -print0 | sort -z
)

((${#perl_modules[@]} > 0)) || fail "no bundled Perl modules found"

for module in "${perl_modules[@]}"; do
    rel=${module#"$root"/}
    run_logged "syntax $rel" \
        env -u PERL5LIB perl -I"$root/Modules" -c "$module"
done

run_logged "Variance-sliding embedded tests" \
    bash -c \
    'cd "$1" && env -u PERL5LIB perl "$2/Variance-sliding.pl" --test' \
    _ "$tmpdir" "$root"

run_logged "trim-fastq embedded tests" \
    bash -c \
    'cd "$1" && env -u PERL5LIB perl "$2/basic-pipeline/trim-fastq.pl" --test' \
    _ "$tmpdir" "$root"

run_logged "R runtime" \
    Rscript -e \
    'stopifnot(getRversion() >= package_version("2.7.0"))'

case ":$PATH:" in
    *":$root:"*)
        echo "NOTE: PoPoolation is in PATH, but the tests did not rely on it"
        ;;
    *)
        pass "no PoPoolation PATH entry required"
        ;;
esac

case ":${PERL5LIB:-}:" in
    *":$root/Modules:"*)
        echo "NOTE: Modules is in PERL5LIB, but clean tests did not rely on it"
        ;;
    *)
        pass "no PoPoolation PERL5LIB entry required"
        ;;
esac

printf '\nAll PoPoolation smoke tests passed.\n'