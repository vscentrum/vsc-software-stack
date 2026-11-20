
#!/usr/bin/env bash
# Smoke test for GAMESS-US 20240715-R2
# Run after loading the GAMESS-US EasyBuild module.

set -euo pipefail

VERSION="20240715-R2"
NCPUS="${1:-2}"
TIMEOUT="${GAMESS_TEST_TIMEOUT:-120}"

# Check that the module is loaded.
if [[ -z "${GAMESSUSROOT:-}" ]]; then
    echo "FAIL: GAMESS-US module is not loaded."
    exit 1
fi

GMS="$GAMESSUSROOT"

# Check required files.
for file in \
    "$GMS/rungms" \
    "$GMS/gamess.$VERSION.x" \
    "$GMS/tests/standard/exam01.inp"
do
    if [[ ! -f "$file" ]]; then
        echo "FAIL: Missing file: $file"
        exit 1
    fi
done

if ! [[ "$NCPUS" =~ ^[1-9][0-9]*$ ]]; then
    echo "FAIL: NCPUS must be a positive integer."
    exit 1
fi

# Create an isolated temporary working directory.
WORKDIR=$(mktemp -d "${TMPDIR:-/tmp}/gamess-smoke.XXXXXXXX")
LOGFILE="$WORKDIR/exam01.log"

mkdir -p "$WORKDIR/scratch" "$WORKDIR/userscr"

cp "$GMS/tests/standard/exam01.inp" "$WORKDIR/"

export SCR="$WORKDIR/scratch"
export USERSCR="$WORKDIR/userscr"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

echo "======================================"
echo " GAMESS-US Smoke Test"
echo "======================================"
echo "Version:       $VERSION"
echo "Installation:  $GMS"
echo "Compute ranks: $NCPUS"
echo "MPI ranks:     $((2 * NCPUS))"
echo "Working dir:   $WORKDIR"
echo

# Run the official GAMESS test input.
STATUS=0
(
    cd "$WORKDIR"
    timeout -k 5s "${TIMEOUT}s" \
        "$GMS/rungms" exam01.inp \
        "$VERSION" "$NCPUS" "$NCPUS"
) > "$LOGFILE" 2>&1 || STATUS=$?

# Verify execution and expected MPI/DDI configuration.
if [[ "$STATUS" -eq 0 ]] &&
   grep -q "EXECUTION OF GAMESS TERMINATED NORMALLY" "$LOGFILE" &&
   grep -q "MPI will run $NCPUS compute processes and $NCPUS data servers" "$LOGFILE" &&
   ! grep -q "MPI_ABORT was invoked" "$LOGFILE"; then

    echo "PASS: GAMESS calculation completed."
    grep -E "MPI will run|EXECUTION OF GAMESS TERMINATED NORMALLY" "$LOGFILE"
    echo
    echo "GAMESS-US smoke test: PASSED"

    # Keep files only if requested.
    if [[ "${KEEP_WORKDIR:-0}" != "1" ]]; then
        rm -rf -- "$WORKDIR"
    else
        echo "Results preserved in: $WORKDIR"
    fi
else
    echo "FAIL: GAMESS smoke test failed."
    echo "Exit code: $STATUS"
    echo
    echo "Last 50 lines of output:"
    tail -n 50 "$LOGFILE"
    echo
    echo "Results preserved in: $WORKDIR"
    exit 1
fi
