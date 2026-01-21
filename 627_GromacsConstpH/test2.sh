set -e
workdir=$(mktemp -d)
cd "$workdir"

cat > md.mdp <<'EOF'
integrator  = md
dt          = 0.002
nsteps      = 200
nstxout-compressed = 0
nstenergy   = 10
nstlog      = 10
cutoff-scheme = Verlet
nstlist     = 10
coulombtype = PME
rcoulomb    = 1.0
rvdw        = 1.0
pbc         = xyz
constraints = h-bonds
tcoupl      = v-rescale
tc-grps     = System
tau_t       = 0.1
ref_t       = 300
pcoupl      = no
EOF

gmx solvate -cs spc216.gro -box 2 2 2 -o conf.gro
gmx grompp -f md.mdp -c conf.gro -p topol.top -o md.tpr -maxwarn 1

# PLUMED: super simple - just print a constant and the step
cat > plumed.dat <<'EOF'
PRINT STRIDE=10 ARG=* FILE=COLVAR
EOF

# Run with PLUMED + GPU
gmx mdrun -deffnm md -v -nb gpu -bonded gpu -update gpu -pme cpu -pin on -plumed plumed.dat 2>&1 | tee mdrun.log

# Evidence
test -f COLVAR
head -n 5 COLVAR
grep -i -E "plumed|patched|COLVAR" -n mdrun.log | head -n 40
echo "Artifacts in: $workdir"
