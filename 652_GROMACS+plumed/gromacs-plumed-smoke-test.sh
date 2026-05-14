#!/bin/bash
set -euo pipefail

test -n "${PLUMED_KERNEL:-}"
test -f "$PLUMED_KERNEL"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
cd "$tmpdir"

{
    echo "PLUMED smoke test"
    echo "2"
    printf "%5d%-5s%5s%5d%8.3f%8.3f%8.3f\n" 1 ARG AR1 1 0.000 0.000 0.000
    printf "%5d%-5s%5s%5d%8.3f%8.3f%8.3f\n" 1 ARG AR2 2 0.500 0.000 0.000
    printf "%10.5f%10.5f%10.5f\n" 4.00000 4.00000 4.00000
} > conf.gro

cat > topol.top <<'EOF'
[ defaults ]
1 1 no 1.0 1.0

[ atomtypes ]
AR 39.948 0.0 A 0.34 0.997

[ moleculetype ]
ARGON2 1

[ atoms ]
1 AR 1 ARG AR1 1 0.0 39.948
2 AR 1 ARG AR2 2 0.0 39.948

[ system ]
PLUMED smoke test

[ molecules ]
ARGON2 1
EOF

cat > md.mdp <<'EOF'
integrator = md
nsteps = 1
dt = 0.001
cutoff-scheme = Verlet
nstlist = 10
rlist = 1.0
rvdw = 1.0
rcoulomb = 1.0
coulombtype = Cut-off
vdwtype = Cut-off
pbc = xyz
tcoupl = no
pcoupl = no
constraints = none
gen_vel = no
nstenergy = 1
nstcalcenergy = 1
nstlog = 1
nstxout = 0
EOF

cat > plumed.dat <<'EOF'
d: DISTANCE ATOMS=1,2
PRINT ARG=d FILE=COLVAR STRIDE=1
DUMPATOMS ATOMS=1,2 FILE=plumed_atoms.xyz PRECISION=17
EOF

gmx -quiet grompp -f md.mdp -c conf.gro -p topol.top -o smoke.tpr
gmx -quiet mdrun -s smoke.tpr -deffnm smoke -plumed plumed.dat -ntmpi 1 -ntomp 1

test -s COLVAR
test -s plumed_atoms.xyz
grep -q '^#! FIELDS.* d' COLVAR
awk 'NF >= 2 && $1 !~ /^#/ {found=1; if ($2 <= 0) exit 2} END {exit found ? 0 : 1}' COLVAR

echo "GROMACS native PLUMED smoke test passed"