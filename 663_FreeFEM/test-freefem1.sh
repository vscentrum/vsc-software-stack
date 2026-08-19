#!/usr/bin/env bash

set -euo pipefail

export LC_ALL=C

: "${EBROOTFREEFEM:?Load the FreeFEM module first}"

version="4.14"
root="$EBROOTFREEFEM"

ff="$root/bin/FreeFem++-nw"
ffmpi="$root/bin/FreeFem++-mpi"

plugindir="$root/lib/ff++/$version/lib"
mpiplugindir="$plugindir/mpi"
examples="$root/share/FreeFEM/$version/examples"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

echo "== FreeFEM smoke test =="
echo "Root: $root"

echo
echo "== Binaries =="

for exe in FreeFem++ FreeFem++-nw FreeFem++-mpi ff-mpirun bamg; do
    test -x "$root/bin/$exe"
    echo "OK: $exe"
done

echo
echo "== Version =="

"$ff" -v 0 2>&1 | head -5 || true

echo
echo "== Serial plugins =="

for plugin in SuperLu mmg; do
    if test -f "$plugindir/$plugin.so"; then
        echo "OK: $plugin.so"
    else
        echo "ERROR: missing $plugindir/$plugin.so" >&2
        exit 1
    fi
done

echo
echo "== MPI plugins =="

for plugin in hpddm hpddm_substructuring PETSc function-PETSc SLEPc parmmg; do
    if test -f "$mpiplugindir/$plugin.so"; then
        echo "OK: $plugin.so"
    else
        echo "ERROR: missing $mpiplugindir/$plugin.so" >&2
        exit 1
    fi
done

echo
echo "== Basic serial solve =="

cat > "$workdir/basic.edp" <<'EOF'
mesh Th = square(12, 12);
fespace Vh(Th, P1);
Vh u, v;

problem poisson(u, v)
    = int2d(Th)(dx(u)*dx(v) + dy(u)*dy(v))
    - int2d(Th)(v)
    + on(1, 2, 3, 4, u=0);

poisson;

cout << "SERIAL_SOLVE_OK" << endl;
EOF

"$ff" -v 0 "$workdir/basic.edp" | tee "$workdir/basic.log"

grep -q 'SERIAL_SOLVE_OK' "$workdir/basic.log"

echo "OK: basic serial solve"

echo
echo "== SuperLU functional test =="

test -f "$examples/plugin/SuperLU.edp"

"$ff" -v 0 "$examples/plugin/SuperLU.edp" \
    | tee "$workdir/superlu.log"

grep -q 'Normal End' "$workdir/superlu.log"

if grep -qiE 'Load error|Error opening' "$workdir/superlu.log"; then
    echo "ERROR: SuperLU example reported a plugin loading error" >&2
    exit 1
fi

echo "OK: SuperLU plugin and solver work"

echo
echo "== MMG plugin loading =="

cat > "$workdir/mmg.edp" <<'EOF'
load "msh3"
load "mmg"

cout << "MMG_LOAD_OK" << endl;
EOF

"$ff" -v 0 "$workdir/mmg.edp" | tee "$workdir/mmg.log"

grep -q 'MMG_LOAD_OK' "$workdir/mmg.log"

echo "OK: MMG plugin loads"

echo
echo "== MPI runtime =="

cat > "$workdir/mpi.edp" <<'EOF'
cout << "MPI_RUNTIME_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/mpi.edp" \
    | tee "$workdir/mpi.log"

mpi_count="$(grep -c 'MPI_RUNTIME_OK' "$workdir/mpi.log" || true)"

if test "$mpi_count" -ne 2; then
    echo "ERROR: expected output from 2 MPI ranks, got $mpi_count" >&2
    exit 1
fi

echo "OK: FreeFEM MPI works with 2 ranks"

echo
echo "== HPDDM plugin loading =="

cat > "$workdir/hpddm.edp" <<'EOF'
load "hpddm"

cout << "HPDDM_LOAD_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/hpddm.edp" \
    | tee "$workdir/hpddm.log"

hpddm_count="$(grep -c 'HPDDM_LOAD_OK' "$workdir/hpddm.log" || true)"

if test "$hpddm_count" -ne 2; then
    echo "ERROR: HPDDM plugin did not load on both MPI ranks" >&2
    exit 1
fi

echo "OK: HPDDM plugin loads"

echo
echo "== HPDDM substructuring plugin loading =="

cat > "$workdir/hpddm-substructuring.edp" <<'EOF'
load "hpddm"
load "hpddm_substructuring"

cout << "HPDDM_SUBSTRUCTURING_LOAD_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/hpddm-substructuring.edp" \
    | tee "$workdir/hpddm-substructuring.log"

hpddm_sub_count="$(
    grep -c 'HPDDM_SUBSTRUCTURING_LOAD_OK' "$workdir/hpddm-substructuring.log" || true
)"

if test "$hpddm_sub_count" -ne 2; then
    echo "ERROR: HPDDM substructuring plugin did not load on both MPI ranks" >&2
    exit 1
fi

echo "OK: HPDDM substructuring plugin loads"

echo
echo "== PETSc plugin loading =="

cat > "$workdir/petsc.edp" <<'EOF'
load "PETSc"

cout << "PETSC_LOAD_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/petsc.edp" \
    | tee "$workdir/petsc.log"

petsc_count="$(grep -c 'PETSC_LOAD_OK' "$workdir/petsc.log" || true)"

if test "$petsc_count" -ne 2; then
    echo "ERROR: PETSc plugin did not load on both MPI ranks" >&2
    exit 1
fi

echo "OK: PETSc plugin loads"

echo
echo "== SLEPc plugin loading =="

cat > "$workdir/slepc.edp" <<'EOF'
load "PETSc"
load "SLEPc"

cout << "SLEPC_LOAD_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/slepc.edp" \
    | tee "$workdir/slepc.log"

slepc_count="$(grep -c 'SLEPC_LOAD_OK' "$workdir/slepc.log" || true)"

if test "$slepc_count" -ne 2; then
    echo "ERROR: SLEPc plugin did not load on both MPI ranks" >&2
    exit 1
fi

echo "OK: SLEPc plugin loads"

echo
echo "== ParMmg plugin loading =="

cat > "$workdir/parmmg.edp" <<'EOF'
load "msh3"
load "parmmg"

cout << "PARMMG_LOAD_OK" << endl;
EOF

mpirun -n 2 "$ffmpi" -nw -v 0 "$workdir/parmmg.edp" \
    | tee "$workdir/parmmg.log"

parmmg_count="$(grep -c 'PARMMG_LOAD_OK' "$workdir/parmmg.log" || true)"

if test "$parmmg_count" -ne 2; then
    echo "ERROR: ParMmg plugin did not load on both MPI ranks" >&2
    exit 1
fi

echo "OK: ParMmg plugin loads"

echo
echo "================================"
echo "All FreeFEM smoke tests passed."
echo "================================"