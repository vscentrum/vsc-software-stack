set -euo pipefail

gmxdat="$EBROOTGROMACS"
topdir="$gmxdat/share/gromacs/top"
work="$(mktemp -d)"
echo "Workdir: $work"

# Prepare coordinates in workdir
cp "$topdir/spc216.gro" "$work/"
cd "$work"
gmx editconf -f spc216.gro -o conf.gro -box 3 3 3

# Minimal mdp
cat > md.mdp <<'EOF'
integrator    = md
nsteps        = 200
dt            = 0.002
cutoff-scheme = Verlet
nstlist       = 10
rlist         = 1.0
rcoulomb      = 1.0
rvdw          = 1.0
coulombtype   = PME
pbc           = xyz
tcoupl        = v-rescale
tc-grps       = System
tau-t         = 1.0
ref-t         = 300
pcoupl        = no
constraints   = h-bonds
EOF

# Topology: include from forcefield directory (avoids the removed top-level spc.itp)
cat > topol.top <<'EOF'
#include "gromos54a7.ff/forcefield.itp"
#include "gromos54a7.ff/spc.itp"

[ system ]
SPC water

[ molecules ]
SOL 216
EOF

# Run grompp from inside share/top so relative includes resolve (no -I needed/available)
cd "$topdir"
gmx grompp -f "$work/md.mdp" -c "$work/conf.gro" -p "$work/topol.top" -o "$work/md.tpr" -maxwarn 1

# Run mdrun on GPU (thread-MPI build: specify -ntmpi)
cd "$work"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
gmx mdrun -deffnm md -v -pin on -nb gpu -pme cpu -ntmpi 1

# Show evidence of GPU usage
grep -E "Using.*GPU|GPU.*detected|Device|CUDA" md.log | head -n 80 || true
echo "OK: CUDA run finished"
