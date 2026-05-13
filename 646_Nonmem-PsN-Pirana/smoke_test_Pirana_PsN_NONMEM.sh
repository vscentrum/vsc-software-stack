#!/usr/bin/env bash
set -Eeuo pipefail

RUN_GUI="${RUN_GUI:-0}"
GUI_TIMEOUT="${GUI_TIMEOUT:-45}"
GUI_LAUNCHER="${GUI_LAUNCHER:-pirana}"
WORKDIR="${WORKDIR:-$(mktemp -d "${TMPDIR:-/tmp}/pirana-psn-nonmem.XXXXXX")}"
PROJECT="$WORKDIR/pirana_project"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

section() {
    echo
    echo "== $* =="
}

extract_ofv() {
    perl -MText::ParseWords -e '
        my $file = shift;
        open my $fh, "<", $file or die "cannot open $file: $!";
        chomp(my $header = <$fh>);
        chomp(my $row = <$fh>);
        my @h = parse_line(",", 0, $header);
        my @v = parse_line(",", 0, $row);
        for my $i (0..$#h) {
            $h[$i] =~ s/^"//; $h[$i] =~ s/"$//;
            if ($h[$i] eq "ofv") {
                print $v[$i], "\n";
                exit 0;
            }
        }
        exit 1;
    ' "$1"
}

check_no_failure_markers() {
    local label="$1"
    shift

    set +e
    grep -HniE 'run failed|NMtran failed|AN ERROR WAS FOUND|PROGRAM TERMINATED|TERMINATED DUE|FATAL ERROR' "$@"
    local status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        fail "failure markers detected for $label"
    fi
}

run_psn_model() {
    local model="$1"
    local base="${model%.mod}"
    local run_dir="runs/${base}"
    local stdout="logs/${base}.stdout"
    local stderr="logs/${base}.stderr"

    section "Running PsN execute for $model"

    set +e
    execute "$model" -dir="$run_dir" > "$stdout" 2> "$stderr"
    local status=$?
    set -e

    if [ "$status" -ne 0 ]; then
        echo "stdout:"
        cat "$stdout" || true
        echo "stderr:"
        cat "$stderr" || true
        fail "execute failed for $model with exit code $status"
    fi

    local lst="$PROJECT/${base}.lst"
    local ext="$PROJECT/${base}.ext"
    local sdtab="$PROJECT/sdtab_${base}"
    local raw="$PROJECT/${run_dir}/raw_results_${base}.csv"

    test -f "$lst" || fail "missing NONMEM lst file: $lst"
    test -f "$ext" || fail "missing NONMEM ext file: $ext"
    test -f "$sdtab" || fail "missing NONMEM table file: $sdtab"
    test -f "$raw" || fail "missing PsN raw results file: $raw"

    check_no_failure_markers "$model" "$stdout" "$stderr" "$lst" "$raw"

    echo "lst: $lst"
    echo "ext: $ext"
    echo "sdtab: $sdtab"
    echo "raw results: $raw"
    echo "raw results preview:"
    head -3 "$raw"

    local ofv
    ofv="$(extract_ofv "$raw")" || fail "could not extract OFV from $raw"
    echo "$ofv" > "logs/${base}.ofv"
    echo "OFV($base)=$ofv"
}

section "Pirana + PsN + NONMEM integration smoke test"
echo "WORKDIR=$WORKDIR"
echo "PROJECT=$PROJECT"
echo "RUN_GUI=$RUN_GUI"
echo "GUI_LAUNCHER=$GUI_LAUNCHER"
echo "GUI_TIMEOUT=$GUI_TIMEOUT"

export R_LIBS_USER=
export R_PROFILE_USER=/dev/null
export R_ENVIRON_USER=/dev/null
export PIRANA_HOME="$WORKDIR/pirana_home"
mkdir -p "$PIRANA_HOME"

section "Environment"
echo "PATH=$PATH"
echo "PERL5LIB=${PERL5LIB:-<unset>}"
echo "PIRANA_LOCALLIB=${PIRANA_LOCALLIB:-<unset>}"
echo "PIRANA_HOME=$PIRANA_HOME"
echo "EBROOTPIRANA=${EBROOTPIRANA:-<unset>}"
echo "EBROOTPSN=${EBROOTPSN:-<unset>}"
echo "EBROOTNONMEM=${EBROOTNONMEM:-<unset>}"
echo "DISPLAY=${DISPLAY:-<unset>}"

section "Required commands"
for cmd in perl Rscript pirana pirana_start execute psn qa nmfe76; do
    command -v "$cmd" >/dev/null 2>&1 || fail "missing command: $cmd; load Pirana module first"
    echo "$cmd -> $(command -v "$cmd")"
done

section "Pirana source and wrapper checks"
test -n "${EBROOTPIRANA:-}" || fail "EBROOTPIRANA is not set"
test -x "$EBROOTPIRANA/bin/pirana" || fail "missing $EBROOTPIRANA/bin/pirana"
test -x "$EBROOTPIRANA/bin/pirana_start" || fail "missing $EBROOTPIRANA/bin/pirana_start"
test -f "$EBROOTPIRANA/pirana/pirana.pl" || fail "missing $EBROOTPIRANA/pirana/pirana.pl"
test -x "$EBROOTPIRANA/pirana/pirana_start" || fail "missing $EBROOTPIRANA/pirana/pirana_start"

perl -c "$EBROOTPIRANA/pirana/pirana.pl"
ldd "$EBROOTPIRANA/pirana/pirana_start" | tee "$WORKDIR/pirana_start.ldd"
if grep -q 'not found' "$WORKDIR/pirana_start.ldd"; then
    fail "pirana_start has unresolved shared libraries"
fi

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

section "PsNR/R check"
Rscript --vanilla -e 'library(PsNR); cat("PsNR", as.character(packageVersion("PsNR")), "OK\n")'

section "PsN/NONMEM command checks"
psn -h >/dev/null
execute -h >/dev/null
qa -h >/dev/null
nmfe76 | grep -E 'Usage|usage|NONMEM' >/dev/null || true

section "Creating small Pirana-style NONMEM project"
mkdir -p "$PROJECT/logs" "$PROJECT/runs" "$PROJECT/notes"
cd "$PROJECT"

cat > README.txt <<'EOF'
Pirana/PsN/NONMEM integration smoke project.

m001_constant.mod:
  constant mean model

m002_time.mod:
  linear TIME effect model

Expected:
  both models run through PsN execute
  m002_time should have a lower OFV than m001_constant
EOF

cat > pirana_demo.csv <<'EOF'
@ID TIME DV
1 0 5.0
1 1 5.7
1 2 6.5
1 4 7.8
1 6 9.4
2 0 4.8
2 1 5.6
2 2 6.2
2 4 7.9
2 6 9.1
3 0 5.2
3 1 5.8
3 2 6.6
3 4 8.1
3 6 9.5
4 0 4.9
4 1 5.5
4 2 6.4
4 4 7.7
4 6 9.0
EOF

cat > m001_constant.mod <<'EOF'
$PROBLEM m001 constant mean model

$INPUT ID TIME DV
$DATA pirana_demo.csv IGNORE=@

$PRED
IPRED = THETA(1)
Y = IPRED + EPS(1)

$THETA
(0,5)

$SIGMA
1

$ESTIMATION METHOD=0 MAXEVAL=999 PRINT=1 NOABORT

$TABLE ID TIME DV IPRED FILE=sdtab_m001_constant NOAPPEND ONEHEADER NOPRINT
EOF

cat > m002_time.mod <<'EOF'
$PROBLEM m002 linear time effect model

$INPUT ID TIME DV
$DATA pirana_demo.csv IGNORE=@

$PRED
IPRED = THETA(1) + THETA(2) * TIME
Y = IPRED + EPS(1)

$THETA
(0,5)
(-10,0.7,10)

$SIGMA
1

$ESTIMATION METHOD=0 MAXEVAL=999 PRINT=1 NOABORT

$TABLE ID TIME DV IPRED FILE=sdtab_m002_time NOAPPEND ONEHEADER NOPRINT
EOF

ls -l

run_psn_model "m001_constant.mod"
run_psn_model "m002_time.mod"

section "Comparing model OFVs"
OFV1="$(cat logs/m001_constant.ofv)"
OFV2="$(cat logs/m002_time.ofv)"
echo "OFV(m001_constant)=$OFV1"
echo "OFV(m002_time)=$OFV2"

perl -e '
    my ($ofv1, $ofv2) = @ARGV;
    die "OFV is not numeric\n" unless $ofv1 =~ /^-?\d+(\.\d+)?([Ee][+-]?\d+)?$/ && $ofv2 =~ /^-?\d+(\.\d+)?([Ee][+-]?\d+)?$/;
    die "Expected m002_time OFV to be lower than m001_constant OFV\n" unless $ofv2 < $ofv1;
    print "OFV comparison OK: m002_time improves over m001_constant\n";
' "$OFV1" "$OFV2"

section "Project output summary"
find "$PROJECT" -maxdepth 3 -type f | sort | sed "s#^$PROJECT/##"

if [ "$RUN_GUI" = "1" ]; then
    section "Optional Pirana GUI launch from generated project"
    [ -n "${DISPLAY:-}" ] || fail "RUN_GUI=1 but DISPLAY is not set"

    echo "Launching $GUI_LAUNCHER from $PROJECT for ${GUI_TIMEOUT}s"
    set +e
    timeout "$GUI_TIMEOUT" "$GUI_LAUNCHER" > "$WORKDIR/${GUI_LAUNCHER}.stdout" 2> "$WORKDIR/${GUI_LAUNCHER}.stderr"
    status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        echo "$GUI_LAUNCHER exited cleanly"
    elif [ "$status" -eq 124 ]; then
        echo "$GUI_LAUNCHER stayed alive until timeout; treating GUI startup as OK"
    else
        echo "$GUI_LAUNCHER stdout:"
        cat "$WORKDIR/${GUI_LAUNCHER}.stdout" || true
        echo "$GUI_LAUNCHER stderr:"
        cat "$WORKDIR/${GUI_LAUNCHER}.stderr" || true
        fail "$GUI_LAUNCHER GUI launch failed with exit code $status"
    fi
else
    section "GUI launch skipped"
    echo "Use RUN_GUI=1 inside a desktop/X11 session to launch Pirana from the generated project."
fi

section "Success"
echo "Pirana source/wrapper checks OK"
echo "Pirana Perl dependency stack OK"
echo "PsNR/R check OK"
echo "PsN execute + NONMEM estimation OK"
echo "Two-model OFV comparison OK"
echo "Project retained at: $PROJECT"