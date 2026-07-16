#!/bin/bash

set -euo pipefail

for cmd in h5cc h5dump; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "ERROR: ${cmd} was not found in PATH"
        exit 1
    fi
done

echo "HDF5 compiler wrapper: $(command -v h5cc)"
echo
h5cc -showconfig

if h5cc -showconfig | grep -Eq 'Parallel HDF5:[[:space:]]+yes'; then
    echo "ERROR: This is a parallel HDF5 build"
    exit 1
fi

workdir=$(mktemp -d "${TMPDIR:-/tmp}/hdf5-smoketest.XXXXXX")
trap 'rm -rf "${workdir}"' EXIT
cd "${workdir}"

cat > test_hdf5.c <<'EOF'
#include <hdf5.h>
#include <stdio.h>

int main(void)
{
    const char *filename = "test.h5";
    const hsize_t dims[1] = {5};
    const int output[5] = {2, 4, 6, 8, 10};
    int input[5] = {0};

    hid_t file = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (file < 0) return 1;

    hid_t space = H5Screate_simple(1, dims, NULL);
    if (space < 0) return 2;

    hid_t dataset = H5Dcreate2(
        file, "/values", H5T_NATIVE_INT, space,
        H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT
    );
    if (dataset < 0) return 3;

    if (H5Dwrite(
            dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL,
            H5P_DEFAULT, output) < 0) return 4;

    if (H5Dclose(dataset) < 0) return 5;
    if (H5Sclose(space) < 0) return 6;
    if (H5Fclose(file) < 0) return 7;

    file = H5Fopen(filename, H5F_ACC_RDONLY, H5P_DEFAULT);
    if (file < 0) return 8;

    dataset = H5Dopen2(file, "/values", H5P_DEFAULT);
    if (dataset < 0) return 9;

    if (H5Dread(
            dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL,
            H5P_DEFAULT, input) < 0) return 10;

    for (int i = 0; i < 5; i++) {
        if (input[i] != output[i]) {
            fprintf(stderr, "Mismatch at index %d: expected %d, received %d\n",
                    i, output[i], input[i]);
            return 11;
        }
    }

    if (H5Dclose(dataset) < 0) return 12;
    if (H5Fclose(file) < 0) return 13;

    printf("HDF5 C round-trip test passed\n");
    return 0;
}
EOF

echo
echo "Compiling C smoke test..."
h5cc -Wall -Wextra -O2 test_hdf5.c -o test_hdf5

echo "Running C smoke test..."
./test_hdf5

echo "Inspecting generated HDF5 file..."
h5dump -d /values test.h5

if command -v h5fc >/dev/null 2>&1; then
    cat > test_hdf5.f90 <<'EOF'
program test_hdf5
    use hdf5
    implicit none

    integer(hid_t) :: file_id, dataset_id, dataspace_id
    integer(hsize_t), dimension(1) :: dims
    integer, dimension(5) :: output, input
    integer :: error

    dims = [5_hsize_t]
    output = [2, 4, 6, 8, 10]
    input = 0

    call h5open_f(error)
    if (error /= 0) error stop 1

    call h5fcreate_f("test-fortran.h5", H5F_ACC_TRUNC_F, file_id, error)
    if (error /= 0) error stop 2

    call h5screate_simple_f(1, dims, dataspace_id, error)
    if (error /= 0) error stop 3

    call h5dcreate_f(file_id, "values", H5T_NATIVE_INTEGER, dataspace_id, &
        dataset_id, error)
    if (error /= 0) error stop 4

    call h5dwrite_f(dataset_id, H5T_NATIVE_INTEGER, output, dims, error)
    if (error /= 0) error stop 5

    call h5dclose_f(dataset_id, error)
    call h5sclose_f(dataspace_id, error)
    call h5fclose_f(file_id, error)

    call h5fopen_f("test-fortran.h5", H5F_ACC_RDONLY_F, file_id, error)
    if (error /= 0) error stop 6

    call h5dopen_f(file_id, "values", dataset_id, error)
    if (error /= 0) error stop 7

    call h5dread_f(dataset_id, H5T_NATIVE_INTEGER, input, dims, error)
    if (error /= 0) error stop 8

    if (any(input /= output)) error stop 9

    call h5dclose_f(dataset_id, error)
    call h5fclose_f(file_id, error)
    call h5close_f(error)

    print *, "HDF5 Fortran round-trip test passed"
end program test_hdf5
EOF

    echo
    echo "HDF5 Fortran wrapper: $(command -v h5fc)"
    echo "Compiling Fortran smoke test..."
    h5fc -O2 test_hdf5.f90 -o test_hdf5_fortran

    echo "Running Fortran smoke test..."
    ./test_hdf5_fortran
else
    echo
    echo "INFO: h5fc is unavailable; skipping the Fortran interface test"
fi

echo
echo "All available serial HDF5 smoke tests passed"