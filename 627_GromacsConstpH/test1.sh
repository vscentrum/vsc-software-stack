set -e
workdir=$(mktemp -d)
cd "$workdir"

# 2a) Make a tiny box of water
cat > min.mdp <<'EOF'
integrator  = steep
nsteps      = 200
emtol       = 1000
cutoff-scheme = Verlet
nstlist     = 10
coulombtype = PME
rcoulomb    = 1.0
rvdw        = 1.0
pbc         = xyz
constraints = h-bonds
EOF

gmx solvate -cs spc216.gro -box 2 2 2 -o conf.gro
gmx grompp -f min.mdp -c conf.gro -p topol.top -o em.tpr -maxwarn 1

# 2b) Run on GPU (nonbonded/bonded/update on GPU, PME on CPU to keep it simple)
gmx mdrun -deffnm em -v -nb gpu -bonded gpu -update gpu -pme cpu -pin on 2>&1 | tee mdrun.log

# Quick evidence lines
grep -E "GPU|CUDA|Device|Nonbonded|bonded|update|PME" -n mdrun.log | head -n 60
echo "Artifacts in: $workdir"
