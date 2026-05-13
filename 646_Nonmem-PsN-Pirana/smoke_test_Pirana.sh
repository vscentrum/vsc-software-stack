#!/usr/bin/env bash
set -Eeuo pipefail

RUN_GUI="${RUN_GUI:-0}"
GUI_TIMEOUT="${GUI_TIMEOUT:-30}"
TEST_HOME="${TEST_HOME:-$(mktemp -d "${TMPDIR:-/tmp}/pirana-home.XXXXXX")}"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

section() {
    echo
    echo "== $* =="
}

section "Pirana smoke test"
echo "RUN_GUI=$RUN_GUI"
echo "TEST_HOME=$TEST_HOME"

export PIRANA_HOME="$TEST_HOME"
export R_LIBS_USER=
export R_PROFILE_USER=/dev/null
export R_ENVIRON_USER=/dev/null

section "Environment"
echo "PATH=$PATH"
echo "PERL5LIB=${PERL5LIB:-<unset>}"
echo "PIRANA_LOCALLIB=${PIRANA_LOCALLIB:-<unset>}"
echo "PIRANA_HOME=${PIRANA_HOME:-<unset>}"
echo "EBROOTPIRANA=${EBROOTPIRANA:-<unset>}"
echo "EBROOTPSN=${EBROOTPSN:-<unset>}"
echo "EBROOTNONMEM=${EBROOTNONMEM:-<unset>}"
echo "DISPLAY=${DISPLAY:-<unset>}"

section "Required commands"
for cmd in perl pirana pirana_start; do
    command -v "$cmd" >/dev/null 2>&1 || fail "missing command: $cmd; load the Pirana module first"
    echo "$cmd -> $(command -v "$cmd")"
done

test -n "${EBROOTPIRANA:-}" || fail "EBROOTPIRANA is not set"
test -x "$EBROOTPIRANA/bin/pirana" || fail "$EBROOTPIRANA/bin/pirana missing or not executable"
test -x "$EBROOTPIRANA/bin/pirana_start" || fail "$EBROOTPIRANA/bin/pirana_start missing or not executable"
test -f "$EBROOTPIRANA/pirana/pirana.pl" || fail "$EBROOTPIRANA/pirana/pirana.pl missing"
test -x "$EBROOTPIRANA/pirana/pirana_start" || fail "$EBROOTPIRANA/pirana/pirana_start missing or not executable"

section "pirana_start linkage"
ldd "$EBROOTPIRANA/pirana/pirana_start" | tee "$TEST_HOME/pirana_start.ldd"
if grep -q 'not found' "$TEST_HOME/pirana_start.ldd"; then
    fail "pirana_start has missing shared libraries"
fi

section "Perl syntax check"
perl -c "$EBROOTPIRANA/pirana/pirana.pl"

section "Pirana Perl dependency check"
perl \
    -MFile::chdir \
    -MDate::Manip \
    -MLog::Log4perl \
    -MLog::Dispatch::FileRotate \
    -MConfig::Simple \
    -MText::Diff \
    -MText::Diff::HTML \
    -MText::Table \
    -MTk \
    -MTk::ItemStyle \
    -MTk::Pane \
    -MTk::Splashscreen \
    -MTk::JComboBox \
    -MTk::PlotDataset \
    -MTk::HdrResizeButton \
    -MNet::EmptyPort \
    -MCrypt::URandom \
    -MCrypt::CBC \
    -MCrypt::Cipher::DES \
    -MDBI \
    -MDBD::SQLite \
    -MModule::ScanDeps \
    -MImage::Size \
    -MXML::TreePP \
    -MHTTP::Date \
    -MStatistics::R \
    -MData::Compare \
    -MDate::Parse \
    -MList::MoreUtils \
    -MTest::Most \
    -MTest::Files \
    -MHash::Merge::Simple \
    -MGetopt::ArgvFile \
    -MIPC::Run3 \
    -MPAR \
    -MPAR::Dist \
    -MPAR::Packer \
    -MURL::Encode \
    -MLWP::Protocol::https \
    -MSys::Info \
    -e 'print "Pirana Perl deps OK\n"'

section "Integrated NONMEM/PsN visibility"
if command -v psn >/dev/null 2>&1; then
    echo "psn -> $(command -v psn)"
    psn -h >/dev/null
else
    echo "warning: psn not found in PATH"
fi

if command -v execute >/dev/null 2>&1; then
    echo "execute -> $(command -v execute)"
    execute -h >/dev/null
else
    echo "warning: execute not found in PATH"
fi

if command -v nmfe76 >/dev/null 2>&1; then
    echo "nmfe76 -> $(command -v nmfe76)"
else
    echo "warning: nmfe76 not found in PATH"
fi

section "Wrapper inspection"
head -20 "$EBROOTPIRANA/bin/pirana"
head -20 "$EBROOTPIRANA/bin/pirana_start"

if [ "$RUN_GUI" = "1" ]; then
    section "GUI launch test"

    if [ -z "${DISPLAY:-}" ]; then
        fail "RUN_GUI=1 but DISPLAY is not set"
    fi

    echo "Launching source-mode Pirana for ${GUI_TIMEOUT}s..."
    set +e
    timeout "$GUI_TIMEOUT" pirana > "$TEST_HOME/pirana.stdout" 2> "$TEST_HOME/pirana.stderr"
    status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        echo "pirana exited cleanly"
    elif [ "$status" -eq 124 ]; then
        echo "pirana stayed alive until timeout; treating this as GUI launch OK"
    else
        echo "pirana stdout:"
        cat "$TEST_HOME/pirana.stdout" || true
        echo "pirana stderr:"
        cat "$TEST_HOME/pirana.stderr" || true
        fail "pirana GUI launch failed with exit code $status"
    fi

    echo "Launching upstream pirana_start for ${GUI_TIMEOUT}s..."
    set +e
    timeout "$GUI_TIMEOUT" pirana_start > "$TEST_HOME/pirana_start.stdout" 2> "$TEST_HOME/pirana_start.stderr"
    status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        echo "pirana_start exited cleanly"
    elif [ "$status" -eq 124 ]; then
        echo "pirana_start stayed alive until timeout; treating this as GUI launch OK"
    else
        echo "pirana_start stdout:"
        cat "$TEST_HOME/pirana_start.stdout" || true
        echo "pirana_start stderr:"
        cat "$TEST_HOME/pirana_start.stderr" || true
        fail "pirana_start GUI launch failed with exit code $status"
    fi
else
    section "GUI launch test skipped"
    echo "Set RUN_GUI=1 inside an X11/desktop session to test GUI startup."
fi

section "Success"
echo "Pirana Perl/source-mode checks OK"
echo "pirana_start linkage OK"
echo "Pirana/PsN/NONMEM command visibility checked"
echo "PIRANA_HOME test directory retained at: $TEST_HOME"