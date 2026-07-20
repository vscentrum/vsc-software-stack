#!/bin/bash

set -euo pipefail

for cmd in pymolcas nm; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "ERROR: ${cmd} was not found in PATH"
        exit 1
    fi
done

if [[ -z "${MOLCAS:-}" || ! -d "${MOLCAS}" ]]; then
    echo "ERROR: MOLCAS is not set to a valid OpenMolcas installation"
    exit 1
fi

echo

echo "=== QCMaquis interface check ==="

qcm_library="${MOLCAS}/lib/librasscf.so"

if [[ ! -f "${qcm_library}" ]]; then
    echo "ERROR: ${qcm_library} was not found"
    exit 1
fi

if ! nm -D --defined-only "${qcm_library}" 2>/dev/null |
    grep -Eq '[[:space:]]qcmaquis_rdinp_$'; then
    echo "ERROR: QCMaquis interface symbol qcmaquis_rdinp_ was not found"
    exit 1
fi

echo "QCMaquis interface symbol found in librasscf.so"

workdir=$(mktemp -d "${TMPDIR:-/tmp}/openmolcas-smoketest.XXXXXX")

cleanup()
{
    rc=$?

    if [[ ${rc} -eq 0 ]]; then
        rm -rf "${workdir}"
    else
        echo
        echo "ERROR: smoke test failed"
        echo "Logs and scratch files were retained in:"
        echo "  ${workdir}"
    fi
}

trap cleanup EXIT

export MOLCAS_NPROCS=1
export MOLCAS_THREADS="${MOLCAS_THREADS:-2}"
export OMP_NUM_THREADS="${MOLCAS_THREADS}"
export MOLCAS_MEM="${MOLCAS_MEM:-2048}"
export MOLCAS_DISK="${MOLCAS_DISK:-10000}"
export MOLCAS_TIMELIM="${MOLCAS_TIMELIM:-1800}"

echo "OpenMolcas root: ${MOLCAS}"
echo "pymolcas:       $(command -v pymolcas)"
echo "OpenMP threads: ${MOLCAS_THREADS}"

libmolcas="${MOLCAS}/lib/libmolcas.so"

if [[ -e "${libmolcas}" ]]; then
    echo
    echo "=== Libxc symbol ABI check ==="

    if nm -D --undefined-only "${libmolcas}" 2>/dev/null |
        grep -q 'xc_f03_lib_m_MP_'; then
        echo "ERROR: libmolcas.so contains incompatible uppercase _MP_ Libxc references"
        nm -D --undefined-only "${libmolcas}" |
            grep 'xc_f03_lib_m_MP_' |
            head
        exit 1
    fi

    lowercase_refs=$(
        nm -D --undefined-only "${libmolcas}" 2>/dev/null |
            grep -c 'xc_f03_lib_m_mp_' || true
    )

    echo "No incompatible xc_f03_lib_m_MP_* references found"
    echo "Lowercase xc_f03_lib_m_mp_* references: ${lowercase_refs}"
fi

for exe in scf.exe rasscf.exe; do
    path="${MOLCAS}/bin/${exe}"

    if [[ ! -x "${path}" ]]; then
        echo "ERROR: expected executable was not found: ${path}"
        exit 1
    fi

    if command -v ldd >/dev/null 2>&1; then
        missing=$(ldd "${path}" 2>/dev/null | grep 'not found' || true)

        if [[ -n "${missing}" ]]; then
            echo "ERROR: unresolved shared-library dependencies for ${exe}:"
            echo "${missing}"
            exit 1
        fi
    fi
done

cat >"${workdir}/libxc.input" <<'EOF'
* Small B3LYP calculation exercising the external Libxc Fortran interface

&GATEWAY
Coord
1

H 0.0 0.0 0.0
Basis
ANO-S-VDZ
Group
y xz
NoCD

&SEWARD

&SCF
OneGrid
UHF
KSDFT=HYB_GGA_XC_B3LYP

>>FILE checkfile
* OpenMolcas Libxc smoke-test references

#>> 1
#> POTNUC="0.0"/12

#>> 2
#> POTNUC="0.0"/12
#> SEWARD_KINETIC="0.588103730668"/5
#> SEWARD_ATTRACT="-1.084170720692"/5

#>> 3
#> E_SCF="-0.502183814081"/7
#> DFT_ENERGY="-0.249644717091"/6
#> NQ_DENSITY="1.0"/7
>>EOF
EOF

cat >"${workdir}/dmrg.input" <<'EOF'
* Molecule: N2
* Basis: cc-pVDZ
* Features tested: QCMaquis DMRG-SCF

&GATEWAY
Coord
2
Angstrom
N  0.000000  0.000000  -0.54880
N  0.000000  0.000000   0.54880
Basis=cc-pVDZ

&SEWARD

&SCF

&DMRGSCF &END
ActiveSpaceOptimizer=QCMaquis
DMRGSettings
  conv_thresh        = 1e-4
  truncation_final   = 1e-5
  ietl_jcd_tol       = 1e-6
  nsweeps            = 4
  max_bond_dimension = 100
EndDMRGSettings
OOptimizationSettings
  inactive = 2 0 0 0 2 0 0 0
  RAS2     = 1 1 1 0 1 1 1 0
  ITER     = 15,100
  SOCC     = 2,2,2,0,0,0
  LINEAR
EndOOptimizationSettings

>>FILE checkfile
* OpenMolcas QCMaquis smoke-test references

#>> 1
#> POTNUC="23.623982613571"/10

#>> 2
#> POTNUC="23.623982613571"/10
#> SEWARD_KINETIC="22.142349036052"/5
#> SEWARD_ATTRACT="-49.955418932079"/5

#>> 3
#> E_SCF="-108.954141691117"/7

#>> 4
#> E_RASSCF="-109.090016232269"/5
>>EOF
EOF

run_test()
{
    label=$1
    input=$2

    run_dir="${workdir}/run-${label}"
    scratch_dir="${run_dir}/scratch"
    logfile="${run_dir}/${label}.log"

    mkdir -p "${run_dir}" "${scratch_dir}"

    echo
    echo "=== Running ${label} smoke test ==="

    if ! (
        cd "${run_dir}"

        export Project="smoketest_${label}"
        export WorkDir="${scratch_dir}"
        export MOLCAS_OUTPUT=WORKDIR
        export MOLCAS_TEST=CHECK
        export MOLCAS_CHECK_FUZZY=YES
        export MOLCAS_VALIDATE=YES
        export MOLCAS_KEEP_WORKDIR=YES

        pymolcas --ignore_environment "${input}"
    ) >"${logfile}" 2>&1; then
        cat "${logfile}"
        echo
        echo "ERROR: ${label} smoke test failed"
        return 1
    fi

    cat "${logfile}"
    echo
    echo "${label} smoke test passed"
}

run_test libxc "${workdir}/libxc.input"
run_test dmrg "${workdir}/dmrg.input"

echo
echo "All OpenMolcas smoke tests passed:"
echo "  Libxc B3LYP calculation"
echo "  QCMaquis DMRG-SCF calculation"