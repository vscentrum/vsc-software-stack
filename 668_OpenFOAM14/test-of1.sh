#!/usr/bin/env bash

# Smoke test for EasyBuild OpenFOAM 14 installation.
#
# Default:
#   OpenFOAM/14-foss-2026.1
#   4 MPI ranks
#
# Optional:
#   OF_MODULE=OpenFOAM/14-foss-2026.1 NPROCS=8 ./OpenFOAM-14-smoketest.sh
#   KEEP_WORKDIR=1 ./OpenFOAM-14-smoketest.sh
#
# The work directory is preserved automatically if any test fails.

set -o pipefail

OF_MODULE="${OF_MODULE:-OpenFOAM/14-foss-2026.1}"
NPROCS="${NPROCS:-4}"
KEEP_WORKDIR="${KEEP_WORKDIR:-0}"

BASE_TMP="${TMPDIR:-/tmp}"
WORKDIR="${WORKDIR:-$(mktemp -d "${BASE_TMP%/}/openfoam14-smoke.XXXXXX")}"
LOGDIR="$WORKDIR/logs"

mkdir -p "$LOGDIR"

PASSES=0
FAILURES=0
WARNINGS=0

pass()
{
    printf '[PASS] %s\n' "$*"
    PASSES=$((PASSES + 1))
}

fail()
{
    printf '[FAIL] %s\n' "$*" >&2
    FAILURES=$((FAILURES + 1))
}

warn()
{
    printf '[WARN] %s\n' "$*" >&2
    WARNINGS=$((WARNINGS + 1))
}

info()
{
    printf '[INFO] %s\n' "$*"
}

cleanup()
{
    if [ "$KEEP_WORKDIR" = "1" ] || [ "$FAILURES" -gt 0 ]; then
        printf '\nWork directory preserved at:\n  %s\n' "$WORKDIR"
    else
        rm -rf "$WORKDIR"
    fi
}
trap cleanup EXIT


check_command()
{
    local cmd="$1"

    if command -v "$cmd" >/dev/null 2>&1; then
        pass "Command available: $cmd -> $(command -v "$cmd")"
    else
        fail "Command not found: $cmd"
    fi
}


check_linkage()
{
    local object="$1"
    local description="$2"
    local output

    if [ ! -e "$object" ]; then
        fail "$description does not exist: $object"
        return
    fi

    output="$(ldd "$object" 2>&1 || true)"

    if grep -q 'not found' <<< "$output"; then
        fail "$description has unresolved shared libraries"
        printf '%s\n' "$output" >&2
    else
        pass "$description has no unresolved shared libraries"
    fi
}


find_openfoam_library()
{
    local pattern="$1"

    find "$FOAM_LIBBIN" \
        -maxdepth 3 \
        \( -type f -o -type l \) \
        -name "$pattern" \
        -print \
        -quit 2>/dev/null
}


check_openfoam_library()
{
    local description="$1"
    local pattern="$2"
    local library

    library="$(find_openfoam_library "$pattern")"

    if [ -n "$library" ]; then
        pass "$description found: $library"
        check_linkage "$library" "$description"
    else
        fail "$description not found (pattern: $pattern)"
    fi
}


write_decompose_dict()
{
    local path="$1"
    local method="$2"
    local nprocs="$3"
    local libs=""

    case "$method" in
        metis)
            libs='libs ("libmetisDecomp.so");'
            ;;
        scotch)
            libs=""
            ;;
        *)
            fail "Unsupported decomposition method in smoke test: $method"
            return 1
            ;;
    esac

    cat > "$path" <<EOF
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      decomposeParDict;
}

numberOfSubdomains ${nprocs};

${libs}

method ${method};

// ************************************************************************* //
EOF
}


check_bad_solver_output()
{
    local logfile="$1"

    if grep -Eqi \
        'FOAM FATAL|Signal: Floating point exception|Process received signal|Segmentation fault|core dumped' \
        "$logfile"; then

        fail "Fatal solver/runtime error detected in $logfile"
        grep -Ein \
            'FOAM FATAL|Signal: Floating point exception|Process received signal|Segmentation fault|core dumped' \
            "$logfile" | tail -n 30 >&2
        return 1
    fi

    return 0
}


echo "============================================================"
echo " OpenFOAM 14 EasyBuild smoke test"
echo "============================================================"
echo
echo "Module     : $OF_MODULE"
echo "MPI ranks  : $NPROCS"
echo "Work dir   : $WORKDIR"
echo


# ---------------------------------------------------------------------------
# 1. Load the EasyBuild module
# ---------------------------------------------------------------------------

echo "===== 1. MODULE AND ENVIRONMENT ====="

if ! type module >/dev/null 2>&1; then
    if [ -r /etc/profile.d/lmod.sh ]; then
        # shellcheck disable=SC1091
        source /etc/profile.d/lmod.sh
    elif [ -r /etc/profile.d/modules.sh ]; then
        # shellcheck disable=SC1091
        source /etc/profile.d/modules.sh
    fi
fi

if ! type module >/dev/null 2>&1; then
    fail "'module' command is unavailable"
    exit 1
fi

module purge >/dev/null 2>&1 || true

if module load "$OF_MODULE"; then
    pass "Loaded $OF_MODULE"
else
    fail "Could not load $OF_MODULE"
    exit 1
fi

if [ -n "${FOAM_BASH:-}" ] && [ -f "$FOAM_BASH" ]; then
    pass "FOAM_BASH exists: $FOAM_BASH"
else
    fail "FOAM_BASH is missing or invalid: ${FOAM_BASH:-<unset>}"
    exit 1
fi

# shellcheck disable=SC1090
if source "$FOAM_BASH"; then
    pass "Sourced FOAM_BASH"
else
    fail "Failed to source $FOAM_BASH"
    exit 1
fi

if [ "${WM_PROJECT_VERSION:-}" = "14" ]; then
    pass "WM_PROJECT_VERSION = 14"
else
    fail "Unexpected WM_PROJECT_VERSION=${WM_PROJECT_VERSION:-<unset>}"
fi

for var in \
    WM_PROJECT_DIR \
    FOAM_APPBIN \
    FOAM_LIBBIN \
    FOAM_TUTORIALS \
    FOAM_MPI
do
    value="${!var:-}"

    if [ -n "$value" ]; then
        pass "$var = $value"
    else
        fail "$var is not set"
    fi
done

if [ -d "${WM_PROJECT_DIR:-}" ]; then
    pass "WM_PROJECT_DIR exists"
else
    fail "WM_PROJECT_DIR does not exist"
fi

if [ -d "${FOAM_TUTORIALS:-}" ]; then
    pass "FOAM_TUTORIALS exists"
else
    fail "FOAM_TUTORIALS does not exist"
fi


# ---------------------------------------------------------------------------
# 2. Commands and core linkage
# ---------------------------------------------------------------------------

echo
echo "===== 2. EXECUTABLES AND CORE LINKAGE ====="

for cmd in \
    foamRun \
    simpleFoam \
    blockMesh \
    checkMesh \
    decomposePar \
    reconstructPar \
    foamDictionary \
    foamListTimes \
    potentialFoam \
    renumberMesh \
    wmake \
    paraFoam \
    pvdataserver
do
    check_command "$cmd"
done

if command -v foamToVTK >/dev/null 2>&1; then
    pass "Optional command available: foamToVTK"
else
    warn "foamToVTK is not available"
fi

if command -v foamRun >/dev/null 2>&1; then
    check_linkage "$(command -v foamRun)" "foamRun"
fi

if command -v blockMesh >/dev/null 2>&1; then
    check_linkage "$(command -v blockMesh)" "blockMesh"
fi

if command -v decomposePar >/dev/null 2>&1; then
    check_linkage "$(command -v decomposePar)" "decomposePar"
fi

if [ -f "$FOAM_LIBBIN/libOpenFOAM.so" ]; then
    check_linkage "$FOAM_LIBBIN/libOpenFOAM.so" "libOpenFOAM.so"
else
    fail "libOpenFOAM.so not found in $FOAM_LIBBIN"
fi


# ---------------------------------------------------------------------------
# 3. Third-party decomposition support
# ---------------------------------------------------------------------------

echo
echo "===== 3. DECOMPOSITION LIBRARIES ====="

check_openfoam_library \
    "Scotch decomposition library" \
    'libscotchDecomp.so*'

check_openfoam_library \
    "PT-Scotch decomposition library" \
    'libptscotchDecomp.so*'

check_openfoam_library \
    "METIS decomposition library" \
    'libmetisDecomp.so*'

# The Zoltan integration has changed name/role across recent OpenFOAM
# versions, so deliberately accept any OpenFOAM Zoltan shared library.
check_openfoam_library \
    "Zoltan integration library" \
    'libzoltan*.so*'


# ---------------------------------------------------------------------------
# 4. ParaView/OpenFOAM reader integration
# ---------------------------------------------------------------------------

echo
echo "===== 4. PARAVIEW INTEGRATION ====="

if command -v pvdataserver >/dev/null 2>&1; then
    PV_VERSION_OUTPUT="$(pvdataserver --version 2>&1 || true)"
    info "$PV_VERSION_OUTPUT"

    if grep -q '6\.1\.1' <<< "$PV_VERSION_OUTPUT"; then
        pass "ParaView 6.1.1 detected"
    else
        fail "Expected ParaView 6.1.1"
    fi
fi

if [ "${ParaView_VERSION:-}" = "6.1.1" ]; then
    pass "OpenFOAM detected ParaView_VERSION=6.1.1"
else
    fail "OpenFOAM detected unexpected ParaView_VERSION=${ParaView_VERSION:-<unset>}"
fi

if [ -n "${PV_PLUGIN_PATH:-}" ]; then
    pass "PV_PLUGIN_PATH = $PV_PLUGIN_PATH"
else
    fail "PV_PLUGIN_PATH is not set"
fi

PV_READER="${PV_PLUGIN_PATH:-}/libPVFoamReader_SM.so"

if [ -f "$PV_READER" ]; then
    pass "OpenFOAM ParaView reader found: $PV_READER"
    check_linkage "$PV_READER" "OpenFOAM ParaView reader"
else
    fail "OpenFOAM ParaView reader is missing: $PV_READER"
fi


# ---------------------------------------------------------------------------
# 5. Compile and run a tiny downstream OpenFOAM application with wmake
# ---------------------------------------------------------------------------

echo
echo "===== 5. WMAKE DOWNSTREAM BUILD ====="

WMAKE_DIR="$WORKDIR/wmake-smoke"
WMAKE_LOG="$LOGDIR/wmake-smoke.log"
OLD_FOAM_USER_APPBIN="${FOAM_USER_APPBIN:-}"

mkdir -p "$WMAKE_DIR/Make" "$WORKDIR/user-appbin"

export FOAM_USER_APPBIN="$WORKDIR/user-appbin"

cat > "$WMAKE_DIR/ofSmoke.C" <<'EOF'
#include "IOstreams.H"

int main()
{
    Foam::Info
        << "OpenFOAM wmake smoke test OK"
        << Foam::endl;

    return 0;
}
EOF

cat > "$WMAKE_DIR/Make/files" <<'EOF'
ofSmoke.C

EXE = $(FOAM_USER_APPBIN)/ofSmoke
EOF

cat > "$WMAKE_DIR/Make/options" <<'EOF'
EXE_INC = \
    -I$(LIB_SRC)/OpenFOAM/lnInclude

EXE_LIBS = \
    -lOpenFOAM
EOF

if (
    set -e
    cd "$WMAKE_DIR"
    wmake
    "$FOAM_USER_APPBIN/ofSmoke"
) > "$WMAKE_LOG" 2>&1; then

    if grep -q 'OpenFOAM wmake smoke test OK' "$WMAKE_LOG"; then
        pass "wmake compiled and ran a downstream OpenFOAM application"
    else
        fail "wmake application ran but expected output was not found"
    fi
else
    fail "wmake downstream compilation failed"
    tail -n 50 "$WMAKE_LOG" >&2
fi

export FOAM_USER_APPBIN="$OLD_FOAM_USER_APPBIN"


# ---------------------------------------------------------------------------
# Locate the motorBike tutorial used for runtime tests
# ---------------------------------------------------------------------------

MOTORBIKE_SRC="$FOAM_TUTORIALS/incompressibleFluid/motorBike/motorBike"

if [ ! -d "$MOTORBIKE_SRC" ]; then
    fail "OpenFOAM 14 motorBike tutorial not found: $MOTORBIKE_SRC"
    exit 1
fi

pass "motorBike tutorial found"


# ---------------------------------------------------------------------------
# 6. Short serial solver test
# ---------------------------------------------------------------------------

echo
echo "===== 6. SERIAL SOLVER TEST ====="

SERIAL_CASE="$WORKDIR/motorBike-serial"
SERIAL_LOG="$LOGDIR/motorBike-serial.log"

cp -a "$MOTORBIKE_SRC" "$SERIAL_CASE"
chmod -R u+w "$SERIAL_CASE"

cp \
    "$FOAM_TUTORIALS/resources/geometry/motorBike.obj.gz" \
    "$SERIAL_CASE/constant/geometry/"

if (
    set -e
    cd "$SERIAL_CASE"

    foamDictionary system/controlDict \
        -entry startFrom -set startTime

    foamDictionary system/controlDict \
        -entry startTime -set 0

    foamDictionary system/controlDict \
        -entry endTime -set 3

    blockMesh
    checkMesh

    potentialFoam -initialiseUBCs

    # Exercise the native OpenFOAM 14 solver architecture directly.
    foamRun -solver incompressibleFluid
) > "$SERIAL_LOG" 2>&1; then

    pass "Short serial foamRun simulation completed"
else
    fail "Short serial foamRun simulation failed"
    tail -n 80 "$SERIAL_LOG" >&2
fi

if grep -q 'Mesh OK' "$SERIAL_LOG"; then
    pass "Serial blockMesh mesh passed checkMesh"
else
    fail "Serial checkMesh did not report 'Mesh OK'"
fi

if grep -q '^End$' "$SERIAL_LOG"; then
    pass "Serial solver reached normal OpenFOAM termination"
else
    fail "Serial solver did not reach 'End'"
fi

check_bad_solver_output "$SERIAL_LOG" || true


# Test paraFoam without opening a GUI.
PARAFOAM_LOG="$LOGDIR/paraFoam-touch.log"

if (
    cd "$SERIAL_CASE"
    paraFoam -touch
) > "$PARAFOAM_LOG" 2>&1; then

    if compgen -G "$SERIAL_CASE/*.OpenFOAM" >/dev/null; then
        pass "paraFoam created an OpenFOAM case file"
    else
        fail "paraFoam -touch succeeded but no *.OpenFOAM file was created"
    fi
else
    fail "paraFoam -touch failed"
    cat "$PARAFOAM_LOG" >&2
fi


# Optional data-conversion test.
if command -v foamToVTK >/dev/null 2>&1; then
    FOAMTOVTK_LOG="$LOGDIR/foamToVTK.log"

    if (
        cd "$SERIAL_CASE"
        foamToVTK -latestTime
    ) > "$FOAMTOVTK_LOG" 2>&1; then
        pass "foamToVTK converted the serial result"
    else
        fail "foamToVTK failed"
        tail -n 50 "$FOAMTOVTK_LOG" >&2
    fi
fi


# ---------------------------------------------------------------------------
# 7. Explicit Scotch and METIS decomposition tests
# ---------------------------------------------------------------------------

echo
echo "===== 7. DECOMPOSITION BACKEND TESTS ====="

for method in scotch metis
do
    CASE="$WORKDIR/decomp-$method"
    LOG="$LOGDIR/decomp-$method.log"

    cp -a "$MOTORBIKE_SRC" "$CASE"
    chmod -R u+w "$CASE"

    write_decompose_dict \
        "$CASE/system/decomposeParDict" \
        "$method" \
        "$NPROCS"

    if (
        set -e
        cd "$CASE"
        blockMesh
        decomposePar -copyZero
    ) > "$LOG" 2>&1; then

        NFOUND="$(
            find "$CASE" \
                -maxdepth 1 \
                -type d \
                -name 'processor*' \
                | wc -l
        )"

        if [ "$NFOUND" -eq "$NPROCS" ]; then
            pass "$method decomposition produced $NPROCS processor directories"
        else
            fail "$method decomposition produced $NFOUND processors; expected $NPROCS"
        fi
    else
        fail "$method decomposition failed"
        tail -n 80 "$LOG" >&2
    fi
done


# ---------------------------------------------------------------------------
# 8. Short parallel MPI solver test
# ---------------------------------------------------------------------------

echo
echo "===== 8. PARALLEL MPI SOLVER TEST ====="

PAR_CASE="$WORKDIR/motorBike-parallel"
PAR_LOG="$LOGDIR/motorBike-parallel.log"

cp -a "$MOTORBIKE_SRC" "$PAR_CASE"
chmod -R u+w "$PAR_CASE"

cp \
    "$FOAM_TUTORIALS/resources/geometry/motorBike.obj.gz" \
    "$PAR_CASE/constant/geometry/"

write_decompose_dict \
    "$PAR_CASE/system/decomposeParDict" \
    scotch \
    "$NPROCS"

export OMPI_MCA_rmaps_base_oversubscribe=true
export PRTE_MCA_rmaps_default_mapping_policy=:oversubscribe

if (
    set -e
    cd "$PAR_CASE"

    foamDictionary system/controlDict \
        -entry startFrom -set startTime

    foamDictionary system/controlDict \
        -entry startTime -set 0

    foamDictionary system/controlDict \
        -entry endTime -set 10

    foamDictionary system/controlDict \
        -entry writeControl -set timeStep

    foamDictionary system/controlDict \
        -entry writeInterval -set 10

    blockMesh
    decomposePar -copyZero

    find . -type f -iname '*level*' -delete

    mpirun -np "$NPROCS" \
        renumberMesh -parallel -overwrite

    mpirun -np "$NPROCS" \
        potentialFoam -parallel -initialiseUBCs

    # Test the traditional simpleFoam compatibility entry point too.
    mpirun -np "$NPROCS" \
        simpleFoam -parallel

    reconstructPar -latestTime
) > "$PAR_LOG" 2>&1; then

    pass "Parallel MPI motorBike smoke test completed"
else
    fail "Parallel MPI motorBike smoke test failed"
    tail -n 100 "$PAR_LOG" >&2
fi

check_bad_solver_output "$PAR_LOG" || true

if grep -q 'Finalising parallel run' "$PAR_LOG"; then
    pass "OpenFOAM parallel solver finalised normally"
else
    fail "Parallel solver did not report normal finalisation"
fi

if [ -d "$PAR_CASE/10" ]; then
    pass "reconstructPar produced reconstructed time 10"
else
    fail "Reconstructed time 10 was not produced"
fi


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------

echo
echo "============================================================"
echo " OpenFOAM 14 smoke test summary"
echo "============================================================"
printf 'PASS : %d\n' "$PASSES"
printf 'WARN : %d\n' "$WARNINGS"
printf 'FAIL : %d\n' "$FAILURES"

if [ "$FAILURES" -eq 0 ]; then
    echo
    echo "=== PASS: OpenFOAM 14 installation is functional ==="
    exit 0
else
    echo
    echo "=== FAIL: one or more OpenFOAM checks failed ==="
    echo "Inspect logs in:"
    echo "  $LOGDIR"
    exit 1
fi