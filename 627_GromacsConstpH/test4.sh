#!/usr/bin/env bash
set -euo pipefail

export GMXLIB="$EBROOTGROMACS/share/gromacs/top"
export PLUMED_KERNEL="$EBROOTPLUMED/lib/libplumedKernel.so"
export GMX_MAXBACKUP=-1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

w="$(mktemp -d)"
echo "Workdir: $w"
cd "$w"

cp "$GMXLIB/spc216.gro" .

cat > md.mdp <<'EOF'
integrator  = md
dt          = 0.002
nsteps      = 200
cutoff-scheme = Verlet
nstlist     = 20
rlist       = 1.0
coulombtype = PME
rcoulomb    = 1.0
vdwtype     = Cut-off
rvdw        = 1.0
constraints = h-bonds
constraint_algorithm = lincs
tcoupl      = v-rescale
tc-grps     = System
tau_t       = 0.1
ref_t       = 300
gen_vel     = yes
gen_temp    = 300
gen_seed    = -1
nstxout     = 0
nstvout     = 0
nstfout     = 0
nstenergy   = 10
nstlog      = 10
EOF

gmx editconf -f spc216.gro -o conf.gro -box 3 3 3

cat > topol.top <<'EOF'
#include "gromos53a6.ff/forcefield.itp"
#include "gromos53a6.ff/spc.itp"

[ system ]
SPC water

[ molecules ]
SOL 216
EOF

gmx grompp -f md.mdp -c conf.gro -p topol.top -o md.tpr -maxwarn 1

# Quick “is the option really accepted?” check:
gmx mdrun -plumed foo 2>&1 | head -n 20

cat > plumed.dat <<'EOF'
d: DISTANCE ATOMS=1,4
PRINT STRIDE=10 ARG=d FILE=COLVAR
EOF

gmx mdrun -s md.tpr -deffnm md_plumed -v -pin on -nb gpu -pme cpu -ntmpi 1 -ntomp "$OMP_NUM_THREADS" -plumed plumed.dat

test -s COLVAR
echo "OK: PLUMED run produced COLVAR"
head -n 5 COLVAR
