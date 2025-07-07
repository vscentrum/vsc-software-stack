#!/bin/sh

# This .in file is processed at build time into a shell that runs some
# parallel I/O tests for netCDF/HDF5 parallel I/O.

# Ed Hartnett, Dennis Heimbigner, Ward Fisher

set -e

if test "x$srcdir" = x ; then srcdir=`pwd`; fi
. ../test_common.sh

if test "xyes" = "xyes" ; then
  # Load the findplugins function
  . ${builddir}/findplugin.sh
  echo "findplugin.sh loaded"
  echo "${HDF5_PLUGIN_DIR}"

  # Find zstd plugin.
  findplugin h5zstd
  export HDF5_PLUGIN_PATH="${HDF5_PLUGIN_DIR}"
  echo "HDF5_PLUGIN_PATH=$HDF5_PLUGIN_PATH"
fi

echo
echo "Testing MPI parallel I/O with various other mode flags..."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 1 ./tst_mode
echo
echo "Testing MPI parallel I/O without netCDF..."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_mpi_parallel
echo
echo "Testing very simple parallel I/O with 4 processors..."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_parallel
echo
echo "Testing simple parallel I/O with 16 processors..."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 16 ./tst_parallel3
echo
echo "num_proc   time(s)  write_rate(B/s)"
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 1 ./tst_parallel4
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 2 ./tst_parallel4
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_parallel4
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 8 ./tst_parallel4

# These work but are commented out to speed up the testing.
#/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 16 ./tst_parallel4
#/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 32 ./tst_parallel4
#/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 64 ./tst_parallel4
echo
echo "Testing collective writes with some 0 element writes..."
echo "skipped by EasyBuild"

#echo
#echo "Parallel Performance Test for NASA"
#/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_nc4perf

echo
echo "Parallel I/O test for Collective I/O, contributed by HDF Group."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 1 ./tst_simplerw_coll_r
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 2 ./tst_simplerw_coll_r
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_simplerw_coll_r

# Only run these tests if HDF5 supports parallel filters (v1.10.2 and
# later).
if test "yes" = "yes"; then
    echo
    echo "Parallel I/O test with zlib."
    echo "skipped by EasyBuild"

    echo
    echo "Parallel I/O more tests with zlib and szip (if present in HDF5)."
    /apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 1 ./tst_parallel_compress
    echo "skipped by EasyBuild"
fi

echo
echo "Parallel I/O test for quantize feature."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_quantize_par

echo
echo "Parallel I/O test contributed by wkliao from pnetcdf."
/apps/gent/RHEL9/cascadelake-ib/software/OpenMPI/5.0.7-GCC-14.2.0/bin/mpiexec -n 4 ./tst_parallel6

