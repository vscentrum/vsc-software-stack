#!/bin/bash
#SBATCH -J XXXnameXXX
# Unset XXX...XXX values will be empty, and SBATCH without argument is ignored.
#SBATCH XXXextra1XXX:00:00
#SBATCH -n XXXmpinodesXXX
#SBATCH -c XXXthreadsXXX
#SBATCH -e XXXerrfileXXX
#SBATCH -o XXXoutfileXXX
#SBATCH XXXqueueXXX
#SBATCH XXXextra2XXX
#SBATCH XXXextra3XXX

module load RELION/3.1.4-intel-2023a

srun XXXcommandXXX
