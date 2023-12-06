#!/bin/bash
#PBS -N XXXnameXXX
#PBS -l nodes=XXXmpinodesXXX:ppn=XXXthreadsXXX
#PBS -l walltime=XXXextra1XXX:00:00
#PBS -q XXXqueueXXX
#PBS -e XXXerrfileXXX
#PBS -o XXXoutfileXXX

cd $PBS_O_WORKDIR

module load RELION/3.1.0-foss-2019b

mpirun -n XXXmpinodesXXX XXXcommandXXX
