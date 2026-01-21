work=$(mktemp -d)
cd "$work"

gmx editconf -f "$EBROOTGROMACS/share/gromacs/top/spc216.gro" -o conf.gro -box 3 3 3

cat > topol.top <<'EOF'
#include "oplsaa.ff/forcefield.itp"
#include "oplsaa.ff/spc.itp"

[ system ]
SPC water

[ molecules ]
SOL 216
EOF

cat > md.mdp <<'EOF'
integrator  = md
nsteps      = 200
dt          = 0.002
cutoff-scheme = Verlet
nstlist     = 10
rlist       = 1.0
rcoulomb    = 1.0
rvdw        = 1.0
coulombtype = PME
pbc         = xyz
tcoupl      = v-rescale
tc-grps     = System
tau_t       = 1.0
ref_t       = 300
pcoupl      = no
constraints = h-bonds
continuation = no
gen_vel     = yes
gen_temp    = 300
gen_seed    = -1
nstenergy   = 10
nstlog      = 10
EOF

gmx grompp -f md.mdp -c conf.gro -p topol.top -o md.tpr -maxwarn 1

cat > plumed.dat <<'EOF'
d: DISTANCE ATOMS=1,4
PRINT STRIDE=10 ARG=d FILE=COLVAR
EOF

gmx mdrun -s md.tpr -deffnm md_plumed -v -pin on -nb gpu -pme cpu -ntmpi 1 -ntomp 4 -plumed plumed.dat

ls -l md.tpr COLVAR
head -n 5 COLVAR
