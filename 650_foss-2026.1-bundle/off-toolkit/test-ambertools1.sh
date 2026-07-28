#!/usr/bin/env bash
# Lightweight AmberTools smoke test.
# Assumes the AmberTools module and its dependencies are already loaded.

set -euo pipefail

RUN_MPI=${RUN_MPI:-1}
MPIEXEC=${MPIEXEC:-"mpirun -n 2"}

workdir=$(mktemp -d "${TMPDIR:-/tmp}/ambertools-smoke.XXXXXX")
trap 'rm -rf "$workdir"' EXIT
cd "$workdir"

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: required command not found: $1" >&2
        exit 1
    }
}

for cmd in sander sander.MPI cpptraj tleap antechamber MMPBSA.py \
           packmol-memgen parmed pdb4amber quick quick.MPI; do
    require_command "$cmd"
done

cat > water.pdb <<'PDB'
ATOM      1  O   WAT A   1       0.000   0.000   0.000  1.00  0.00           O
ATOM      2  H1  WAT A   1       0.957   0.000   0.000  1.00  0.00           H
ATOM      3  H2  WAT A   1      -0.239   0.927   0.000  1.00  0.00           H
TER
END
PDB

cat > tleap.in <<'LEAP'
source leaprc.water.tip3p
w = loadpdb water.pdb
check w
saveamberparm w water.prmtop water.inpcrd
quit
LEAP

tleap -f tleap.in > tleap.log
[[ -s water.prmtop && -s water.inpcrd ]]

cat > min.in <<'SANDER'
AmberTools smoke test
&cntrl
  imin=1,
  maxcyc=2,
  ncyc=1,
  ntb=0,
  igb=0,
  cut=999.0,
  ntpr=1,
/
SANDER

sander -O -i min.in -p water.prmtop -c water.inpcrd \
    -o sander.out -r sander.rst7 -inf sander.mdinfo

grep -qi 'final results' sander.out
[[ -s sander.rst7 ]]

if [[ "$RUN_MPI" != 0 ]]; then
    read -r -a mpi_cmd <<< "$MPIEXEC"
    "${mpi_cmd[@]}" sander.MPI -O -i min.in -p water.prmtop -c water.inpcrd \
        -o sander-mpi.out -r sander-mpi.rst7 -inf sander-mpi.mdinfo
    grep -qi 'final results' sander-mpi.out
    [[ -s sander-mpi.rst7 ]]
fi

cat > cpptraj.in <<'CPPTRAJ'
parm water.prmtop
trajin sander.rst7
distance OH @O @H1 out distance.dat
trajout water.nc netcdf
run
CPPTRAJ

cpptraj -i cpptraj.in > cpptraj.log
[[ -s distance.dat && -s water.nc ]]

pdb4amber -i water.pdb -o water.cleaned.pdb > pdb4amber.log
[[ -s water.cleaned.pdb ]]

python -s - <<'PY'
import edgembar
import fetkutils
import ndfes
import parmed as pmd
import pdb4amber
import pymsmt
import pytraj as pt
import sander

parm = pmd.load_file('water.prmtop')
assert len(parm.atoms) == 3, len(parm.atoms)

traj = pt.load('water.nc', 'water.prmtop')
assert traj.n_frames == 1, traj.n_frames
assert traj.n_atoms == 3, traj.n_atoms

print('Python API checks passed')
PY

antechamber -h >/dev/null
MMPBSA.py -h >/dev/null
packmol-memgen -h >/dev/null
parmed -h >/dev/null

printf '%s\n' 'AmberTools smoke test PASSED'
