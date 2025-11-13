import sys, traceback, tempfile, inspect
import structuretoolkit as stk
import pyiron
from pyiron_atomistics import Project
from pyiron_atomistics.atomistics.structure import pyxtal as pa_pyxtal

def main():
    ok = True
    try:
        pyiron_version = getattr(pyiron, "__version__", "unknown")
        import pyiron_atomistics
        pyiron_atomistics_version = getattr(pyiron_atomistics, "__version__", "unknown")
        stk_version = getattr(stk, "__version__", "unknown")
        print("pyiron_version", pyiron_version)
        print("pyiron_atomistics_version", pyiron_atomistics_version)
        print("structuretoolkit_version", stk_version)
    except Exception as e:
        ok = False
        print("ERROR_import_versions", repr(e), file=sys.stderr)
        traceback.print_exc()
    try:
        src = inspect.getsource(pa_pyxtal)
        uses_stk = "structuretoolkit.build" in src
        uses_assyst = "assyst.crystals" in src
        backend = "unknown"
        if uses_stk:
            backend = "structuretoolkit.build"
        if uses_assyst:
            backend = "assyst.crystals"
        print("pyiron_atomistics_pyxtal_backend", backend)
        if uses_stk and not hasattr(stk.build, "pyxtal"):
            ok = False
            print("ERROR_backend_mismatch: pyiron_atomistics expects structuretoolkit.build.pyxtal but it is missing", file=sys.stderr)
        if uses_assyst:
            try:
                from assyst.crystals import pyxtal as assyst_pyxtal
                print("assyst_crystals_pyxtal_import_ok", bool(assyst_pyxtal))
            except Exception as e:
                ok = False
                print("ERROR_backend_mismatch: pyiron_atomistics expects assyst.crystals.pyxtal but import failed", repr(e), file=sys.stderr)
    except Exception as e:
        ok = False
        print("ERROR_inspect_pyxtal_backend", repr(e), file=sys.stderr)
        traceback.print_exc()
    try:
        tmp = tempfile.mkdtemp(prefix="pyiron_structures_")
        pr = Project(tmp)
        structure = pr.create.structure.bulk("Al", cubic=True, a=4.05)
        print("created_structure_n_atoms", len(structure))
    except Exception as e:
        ok = False
        print("ERROR_create_structure_via_pyiron", repr(e), file=sys.stderr)
        traceback.print_exc()
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
