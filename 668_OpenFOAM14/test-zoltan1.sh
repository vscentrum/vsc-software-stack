#!/bin/bash

set -eo pipefail

ZOLTAN_MODULE="${ZOLTAN_MODULE:-Zoltan/3.901-foss-2026.1}"

echo "=== Zoltan smoke test ==="
echo "[INFO] Loading ${ZOLTAN_MODULE}"

module load "${ZOLTAN_MODULE}"

fail() {
    echo "[FAIL] $*"
    exit 1
}

ok() {
    echo "[OK] $*"
}

[ -n "${EBROOTZOLTAN:-}" ] || fail "EBROOTZOLTAN is not defined"

echo "[OK] EBROOTZOLTAN=${EBROOTZOLTAN}"

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/zoltan-smoketest.XXXXXX")"

cleanup() {
    rc=$?
    if [ "${KEEP_TMP:-0}" = "1" ] || [ "${rc}" -ne 0 ]; then
        echo "[INFO] Test files kept in ${WORKDIR}"
    else
        rm -rf "${WORKDIR}"
    fi
}
trap cleanup EXIT

echo
echo "--- Installation ---"

[ -f "${EBROOTZOLTAN}/include/zoltan.h" ] ||
    fail "zoltan.h not found"

ok "Found include/zoltan.h"

if [ -f "${EBROOTZOLTAN}/lib/libzoltan.a" ]; then
    ZOLTAN_LIBDIR="${EBROOTZOLTAN}/lib"
elif [ -f "${EBROOTZOLTAN}/lib64/libzoltan.a" ]; then
    ZOLTAN_LIBDIR="${EBROOTZOLTAN}/lib64"
else
    fail "libzoltan.a not found"
fi

ok "Found ${ZOLTAN_LIBDIR}/libzoltan.a"

command -v mpicc >/dev/null 2>&1 || fail "mpicc not found"
command -v mpirun >/dev/null 2>&1 || fail "mpirun not found"

echo "[OK] mpicc:  $(command -v mpicc)"
echo "[OK] mpirun: $(command -v mpirun)"

echo
echo "--- Enabled dependencies ---"

for var in EBROOTPARMETIS EBROOTMETIS EBROOTSCOTCH; do
    value="${!var:-}"
    if [ -n "${value}" ]; then
        echo "[OK] ${var}=${value}"
    else
        echo "[WARN] ${var} is not defined"
    fi
done

echo
echo "--- Zoltan export metadata ---"

for f in \
    "${EBROOTZOLTAN}/include/Makefile.export.zoltan" \
    "${EBROOTZOLTAN}/include/Makefile.export.zoltan.macros"
do
    if [ -f "${f}" ]; then
        echo "[OK] Found ${f}"
    fi
done

echo
echo "--- Compile MPI/Zoltan test ---"

cat > "${WORKDIR}/zoltan_test.c" <<'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <zoltan.h>

typedef struct {
    int rank;
    int nlocal;
} AppData;

static int get_num_obj(void *data, int *ierr)
{
    AppData *app = (AppData *)data;

    *ierr = ZOLTAN_OK;
    return app->nlocal;
}

static void get_obj_list(
    void *data,
    int num_gid_entries,
    int num_lid_entries,
    ZOLTAN_ID_PTR global_ids,
    ZOLTAN_ID_PTR local_ids,
    int wgt_dim,
    float *obj_wgts,
    int *ierr)
{
    AppData *app = (AppData *)data;
    int i;

    (void)wgt_dim;
    (void)obj_wgts;

    for (i = 0; i < app->nlocal; i++) {
        global_ids[i * num_gid_entries] =
            (ZOLTAN_ID_TYPE)(app->rank * 1000 + i);

        if (num_lid_entries > 0) {
            local_ids[i * num_lid_entries] = (ZOLTAN_ID_TYPE)i;
        }
    }

    *ierr = ZOLTAN_OK;
}

static int get_num_geom(void *data, int *ierr)
{
    (void)data;

    *ierr = ZOLTAN_OK;
    return 1;
}

static void get_geom_multi(
    void *data,
    int num_gid_entries,
    int num_lid_entries,
    int num_obj,
    ZOLTAN_ID_PTR global_ids,
    ZOLTAN_ID_PTR local_ids,
    int num_dim,
    double *geom_vec,
    int *ierr)
{
    AppData *app = (AppData *)data;
    int i;

    (void)num_gid_entries;
    (void)global_ids;

    if (num_dim != 1 || num_lid_entries < 1) {
        *ierr = ZOLTAN_FATAL;
        return;
    }

    for (i = 0; i < num_obj; i++) {
        int lid = (int)local_ids[i * num_lid_entries];

        /*
         * Deliberately interleave coordinates:
         *
         * rank 0: 0, 2, 4, ...
         * rank 1: 1, 3, 5, ...
         *
         * RCB therefore needs to redistribute objects.
         */
        geom_vec[i] = (double)(2 * lid + app->rank);
    }

    *ierr = ZOLTAN_OK;
}

static void check_zoltan(int rc, const char *what, int rank)
{
    if (rc != ZOLTAN_OK && rc != ZOLTAN_WARN) {
        fprintf(stderr,
                "[rank %d] [FAIL] %s returned error %d\n",
                rank, what, rc);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
}

int main(int argc, char **argv)
{
    struct Zoltan_Struct *zz;
    AppData app;

    float version = 0.0;
    int rank, size;
    int rc;

    int changes = 0;
    int num_gid_entries = 0;
    int num_lid_entries = 0;

    int num_import = 0;
    int num_export = 0;

    ZOLTAN_ID_PTR import_global_ids = NULL;
    ZOLTAN_ID_PTR import_local_ids = NULL;
    int *import_procs = NULL;
    int *import_to_part = NULL;

    ZOLTAN_ID_PTR export_global_ids = NULL;
    ZOLTAN_ID_PTR export_local_ids = NULL;
    int *export_procs = NULL;
    int *export_to_part = NULL;

    int total_import = 0;
    int total_export = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size != 2) {
        if (rank == 0) {
            fprintf(stderr,
                    "[FAIL] Run this test with exactly 2 MPI ranks\n");
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    rc = Zoltan_Initialize(argc, argv, &version);
    check_zoltan(rc, "Zoltan_Initialize", rank);

    if (rank == 0) {
        printf("[OK] Zoltan initialized, API version %.3f\n", version);
    }

    app.rank = rank;
    app.nlocal = 8;

    zz = Zoltan_Create(MPI_COMM_WORLD);

    if (zz == NULL) {
        fprintf(stderr,
                "[rank %d] [FAIL] Zoltan_Create failed\n",
                rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    check_zoltan(
        Zoltan_Set_Param(zz, "LB_METHOD", "RCB"),
        "LB_METHOD",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "LB_APPROACH", "PARTITION"),
        "LB_APPROACH",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "NUM_GID_ENTRIES", "1"),
        "NUM_GID_ENTRIES",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "NUM_LID_ENTRIES", "1"),
        "NUM_LID_ENTRIES",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "OBJ_WEIGHT_DIM", "0"),
        "OBJ_WEIGHT_DIM",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "RETURN_LISTS", "ALL"),
        "RETURN_LISTS",
        rank);

    check_zoltan(
        Zoltan_Set_Param(zz, "DEBUG_LEVEL", "0"),
        "DEBUG_LEVEL",
        rank);

    Zoltan_Set_Num_Obj_Fn(zz, get_num_obj, &app);
    Zoltan_Set_Obj_List_Fn(zz, get_obj_list, &app);
    Zoltan_Set_Num_Geom_Fn(zz, get_num_geom, &app);
    Zoltan_Set_Geom_Multi_Fn(zz, get_geom_multi, &app);

    rc = Zoltan_LB_Partition(
        zz,
        &changes,
        &num_gid_entries,
        &num_lid_entries,
        &num_import,
        &import_global_ids,
        &import_local_ids,
        &import_procs,
        &import_to_part,
        &num_export,
        &export_global_ids,
        &export_local_ids,
        &export_procs,
        &export_to_part);

    check_zoltan(rc, "Zoltan_LB_Partition", rank);

    printf("[rank %d] imports=%d exports=%d changes=%d\n",
           rank, num_import, num_export, changes);

    MPI_Allreduce(
        &num_import,
        &total_import,
        1,
        MPI_INT,
        MPI_SUM,
        MPI_COMM_WORLD);

    MPI_Allreduce(
        &num_export,
        &total_export,
        1,
        MPI_INT,
        MPI_SUM,
        MPI_COMM_WORLD);

    if (rank == 0) {
        printf("[INFO] Total imports: %d\n", total_import);
        printf("[INFO] Total exports: %d\n", total_export);
    }

    if (total_import <= 0 || total_export <= 0) {
        if (rank == 0) {
            fprintf(stderr,
                    "[FAIL] RCB produced no redistribution\n");
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    if (total_import != total_export) {
        if (rank == 0) {
            fprintf(stderr,
                    "[FAIL] Import/export mismatch: %d != %d\n",
                    total_import, total_export);
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    Zoltan_LB_Free_Part(
        &import_global_ids,
        &import_local_ids,
        &import_procs,
        &import_to_part);

    Zoltan_LB_Free_Part(
        &export_global_ids,
        &export_local_ids,
        &export_procs,
        &export_to_part);

    Zoltan_Destroy(&zz);

    if (rank == 0) {
        printf("[OK] Zoltan RCB partitioning succeeded\n");
        printf("[OK] MPI import/export lists succeeded\n");
        printf("=== Zoltan functional test PASS ===\n");
    }

    MPI_Finalize();
    return 0;
}
EOF

LINK_FLAGS=(
    "-L${ZOLTAN_LIBDIR}"
)

if [ -n "${EBROOTPARMETIS:-}" ]; then
    for d in "${EBROOTPARMETIS}/lib" "${EBROOTPARMETIS}/lib64"; do
        [ -d "${d}" ] && LINK_FLAGS+=("-L${d}")
    done
fi

if [ -n "${EBROOTMETIS:-}" ]; then
    for d in "${EBROOTMETIS}/lib" "${EBROOTMETIS}/lib64"; do
        [ -d "${d}" ] && LINK_FLAGS+=("-L${d}")
    done
fi

if [ -n "${EBROOTSCOTCH:-}" ]; then
    for d in "${EBROOTSCOTCH}/lib" "${EBROOTSCOTCH}/lib64"; do
        [ -d "${d}" ] && LINK_FLAGS+=("-L${d}")
    done
fi

LINK_FLAGS+=(
    "-Wl,--start-group"
    "-lzoltan"
    "-lparmetis"
    "-lmetis"
    "-lptscotch"
    "-lscotch"
    "-lptscotcherr"
    "-lscotcherr"
    "-Wl,--end-group"
    "-lm"
)

echo "[INFO] Link libraries:"
printf '  %s\n' "${LINK_FLAGS[@]}"

mpicc \
    -O2 \
    -Wall \
    -Wextra \
    -I"${EBROOTZOLTAN}/include" \
    "${WORKDIR}/zoltan_test.c" \
    "${LINK_FLAGS[@]}" \
    -o "${WORKDIR}/zoltan_test" ||
    fail "Compilation failed"

ok "Zoltan MPI test compiled"

echo
echo "--- MPI RCB partitioning ---"

mpirun -np 2 "${WORKDIR}/zoltan_test" ||
    fail "Zoltan MPI partitioning test failed"

echo
echo "===================================="
echo "=== PASS: Zoltan smoke test      ==="
echo "===================================="