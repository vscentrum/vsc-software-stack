import sys, traceback
import structuretoolkit as stk
from ase.build import bulk

def main():
    ok = True
    try:
        print("structuretoolkit_version", getattr(stk, "__version__", "unknown"))
    except Exception as e:
        ok = False
        print("ERROR_structuretoolkit_version", repr(e), file=sys.stderr)
        traceback.print_exc()
    try:
        s = bulk("Al", cubic=True)
        cna = stk.analyse.get_adaptive_cna_descriptors(s)
        print("adaptive_cna_len", len(cna))
    except Exception as e:
        ok = False
        print("ERROR_structuretoolkit_analyse", repr(e), file=sys.stderr)
        traceback.print_exc()
    try:
        has_pyxtal = hasattr(stk.build, "pyxtal")
        print("has_build_pyxtal", has_pyxtal)
    except Exception as e:
        ok = False
        print("ERROR_structuretoolkit_build", repr(e), file=sys.stderr)
        traceback.print_exc()
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
