#!/usr/bin/env bash

set -euo pipefail

expected_version='6.11.0'
chid='fds_smoketest'
mpi_ranks=2

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

for cmd in fds mpirun awk grep mktemp wc; do
    command -v "$cmd" >/dev/null 2>&1 ||
        fail "'$cmd' is not available in PATH"
done

fds_exe=$(command -v fds)
mpi_exe=$(command -v mpirun)

if [[ -n ${EBVERSIONFDS:-} && ${EBVERSIONFDS} != "$expected_version" ]]; then
    fail "loaded FDS version is '${EBVERSIONFDS}', expected '$expected_version'"
fi

base_dir=${SMOKETEST_BASEDIR:-$PWD}
[[ -d $base_dir && -w $base_dir ]] ||
    fail "working-directory base '$base_dir' does not exist or is not writable"

workdir=$(mktemp -d "${base_dir%/}/fds-smoketest.XXXXXX")
workdir=$(cd "$workdir" && pwd -P)

cleanup() {
    local rc=$?

    if (( rc == 0 )); then
        if [[ ${KEEP_OUTPUT:-0} == 1 ]]; then
            echo "Output retained in: $workdir"
        else
            rm -rf "$workdir"
        fi
    else
        echo "FDS smoke test FAILED." >&2
        echo "Output retained in: $workdir" >&2
    fi
}

trap cleanup EXIT

cd "$workdir"

cat > "${chid}.fds" <<'EOF'
&HEAD CHID='fds_smoketest', TITLE='FDS MPI combustion smoke test' /

&MESH ID='left',  IJK=10,10,10, XB=0.0,1.0,0.0,1.0,0.0,1.0 /
&MESH ID='right', IJK=10,10,10, XB=1.0,2.0,0.0,1.0,0.0,1.0 /

&TIME T_END=1.0 /

&REAC FUEL='PROPANE', SOOT_YIELD=0.01 /

&SURF ID='BURNER', HRRPUA=250.0 /

&OBST XB=0.4,0.6,0.4,0.6,0.0,0.1 /
&VENT XB=0.4,0.6,0.4,0.6,0.1,0.1, SURF_ID='BURNER' /
&VENT XB=2.0,2.0,0.0,1.0,0.0,1.0, SURF_ID='OPEN' /

&DEVC ID='T_LEFT', XYZ=0.5,0.5,0.5, QUANTITY='TEMPERATURE' /
&DEVC ID='T_RIGHT', XYZ=1.5,0.5,0.5, QUANTITY='TEMPERATURE' /

&DUMP DT_DEVC=0.2, DT_HRR=0.2 /

&TAIL /
EOF

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OMP_STACKSIZE="${OMP_STACKSIZE:-64M}"

echo "FDS executable: $fds_exe"
echo "MPI launcher:   $mpi_exe"
echo "Working dir:    $workdir"
echo "EasyBuild FDS version: ${EBVERSIONFDS:-unavailable}"
echo "EasyBuild FDS root:    ${EBROOTFDS:-unavailable}"
echo "Running $mpi_ranks MPI ranks with $OMP_NUM_THREADS OpenMP thread(s) per rank..."

if ! mpirun -np "$mpi_ranks" "$fds_exe" "${chid}.fds" \
    > "${chid}.log" 2>&1; then
    echo "ERROR: FDS returned a nonzero exit status." >&2
    tail -n 100 "${chid}.log" >&2
    exit 1
fi

out="${chid}.out"
hrr="${chid}_hrr.csv"
devc="${chid}_devc.csv"
smv="${chid}.smv"

for file in "$out" "$hrr" "$devc" "$smv"; do
    [[ -s $file ]] ||
        fail "expected output file '$file' is missing or empty"
done

if ! grep -Fq 'FDS completed successfully' "${chid}.log" &&
   ! grep -Fq 'FDS completed successfully' "$out"; then
    echo "ERROR: successful FDS termination was not reported." >&2
    tail -n 100 "${chid}.log" >&2
    exit 1
fi

if ! grep -Eq \
    "Number of MPI Processes:[[:space:]]+${mpi_ranks}([[:space:]]|$)" \
    "$out"; then
    echo "ERROR: FDS did not report $mpi_ranks MPI processes." >&2
    grep -Ei 'MPI|Number of MPI Processes' "$out" >&2 || true
    exit 1
fi

if ! grep -Eiq \
    'Compiler[[:space:]]*:.*Intel.*Fortran Compiler' \
    "$out"; then
    echo "ERROR: FDS did not report the Intel Fortran compiler." >&2
    grep -Ei 'Compiler[[:space:]]*:' "$out" >&2 || true
    exit 1
fi

if ! grep -Eiq \
    'MPI library version[[:space:]]*:.*Intel.*MPI' \
    "$out"; then
    echo "ERROR: FDS did not report the Intel MPI library." >&2
    grep -Ei 'MPI library version' "$out" >&2 || true
    exit 1
fi

fatal_pattern='ERROR[[:space:]]*\([0-9]+\):|'\
'Numerical Instability|'\
'forrtl:[[:space:]]*(severe|fatal)|'\
'segmentation fault|'\
'SIGSEGV|'\
'SIGABRT|'\
'MPI_ABORT|'\
'BAD TERMINATION'

if grep -Eiq "$fatal_pattern" "${chid}.log" "$out"; then
    echo "ERROR: a fatal FDS, MPI, or runtime error was detected." >&2
    grep -Ei "$fatal_pattern" "${chid}.log" "$out" >&2 || true
    exit 1
fi

if ! awk -F, '
    NR > 2 {
        time = $1
        hrr = $2
        gsub(/[[:space:]"]/, "", time)
        gsub(/[[:space:]"]/, "", hrr)

        if (time ~ /^[-+]?[0-9]*\.?[0-9]+([Ee][-+]?[0-9]+)?$/) {
            if (time + 0 > maximum_time) {
                maximum_time = time + 0
            }
        }

        if (hrr ~ /^[-+]?[0-9]*\.?[0-9]+([Ee][-+]?[0-9]+)?$/ &&
            hrr + 0 > 0) {
            positive_hrr = 1
        }
    }

    END {
        exit maximum_time >= 0.99 && positive_hrr ? 0 : 1
    }
' "$hrr"; then
    fail "HRR output did not reach 1.0 s or contain a positive heat-release rate"
fi

if ! awk -F, '
    NR > 2 {
        time = $1
        gsub(/[[:space:]"]/, "", time)

        if (time ~ /^[-+]?[0-9]*\.?[0-9]+([Ee][-+]?[0-9]+)?$/ &&
            time + 0 > maximum_time) {
            maximum_time = time + 0
        }

        for (field = 2; field <= NF; field++) {
            value = $field
            gsub(/[[:space:]"]/, "", value)

            if (value ~ /^[-+]?[0-9]*\.?[0-9]+([Ee][-+]?[0-9]+)?$/) {
                numeric_device_data = 1
            }
        }
    }

    END {
        exit maximum_time >= 0.99 && numeric_device_data ? 0 : 1
    }
' "$devc"; then
    fail "device output did not reach 1.0 s or contain numeric data"
fi

echo
echo "FDS runtime information:"
grep -Ei \
    '^[[:space:]]*(Revision|Revision Date|Compiler|Compilation Date|'\
'Number of MPI Processes|Number of OpenMP Threads|MPI library version)' \
    "$out" || true

echo
echo "Final HRR data:"
tail -n 3 "$hrr"

echo
echo "Generated output:"
for file in "$out" "$hrr" "$devc" "$smv"; do
    printf '  %-28s %10s bytes\n' "$file" "$(wc -c < "$file")"
done

echo
echo "PASS: FDS ${EBVERSIONFDS:-$expected_version} completed the MPI combustion smoke test."