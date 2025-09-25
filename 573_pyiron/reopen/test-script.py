import importlib, sys, shutil, tempfile, os, numpy as np
pkgs=["pyiron_base","pyiron_lammps","pyiron_vasp","pyscal3","spglib","phonopy","seekpath","h5py","ase","pandas","matplotlib","mendeleev","mp_api","phonopy","pint","scipy","sklearn","seekpath","spglib","structuretoolkit"]
def v(m): 
    try: 
        mod=importlib.import_module(m); from importlib.metadata import version
        return True,f"{m} {version(m)}"
    except Exception as e: 
        return False,f"{m} IMPORT FAIL: {e}"

def test_spglib():
    try:
        import spglib as spg
        a=3.6; lat=[[0,a/2,a/2],[a/2,0,a/2],[a/2,a/2,0]]; pos=[[0,0,0]]; Z=[29]
        ds=spg.get_symmetry_dataset((lat,pos,Z))
        return ds["number"]==225,"spglib spacegroup=225" if ds["number"]==225 else f"spglib got {ds['number']}"
    except Exception as e: return False,f"spglib FAIL: {e}"

def test_seekpath():
    try:
        import seekpath as sk
        a=3.6; lat=[[0,a/2,a/2],[a/2,0,a/2],[a/2,a/2,0]]; pos=[[0,0,0]]; Z=[29]
        out=sk.get_path((lat,pos,Z))
        return bool(out.get("path")),"seekpath path ok"
    except Exception as e: return False,f"seekpath FAIL: {e}"

def test_phonopy():
    try:
        from phonopy import Phonopy; from phonopy.structure.atoms import PhonopyAtoms
        a=5.43; cell=[[0, a/2, a/2],[a/2,0,a/2],[a/2,a/2,0]]
        uc=PhonopyAtoms(symbols=["Si","Si"],cell=cell,scaled_positions=[[0,0,0],[0.25,0.25,0.25]])
        ph=Phonopy(uc,[[2,0,0],[0,2,0],[0,0,2]]); ph.generate_displacements(distance=0.01)
        return True,"phonopy displacements ok"
    except Exception as e: return False,f"phonopy FAIL: {e}"

def test_h5py():
    try:
        import h5py, tempfile
        fn=os.path.join(tempfile.gettempdir(),"pyiron_smoke.h5")
        with h5py.File(fn,"w") as f: f["x"]=np.arange(5)
        with h5py.File(fn,"r") as f: ok=np.all(f["x"][:]==np.arange(5))
        return ok,"h5py rw ok" if ok else "h5py mismatch"
    except Exception as e: return False,f"h5py FAIL: {e}"

def detect_exec(names): 
    for n in names:
        p=shutil.which(n)
        if p: return True,f"{n} -> {p}"
    return False,"not found"

def test_pyiron_base_min():
    try:
        import pyiron_base as pb
        from pyiron_base import Project
        d=tempfile.mkdtemp(prefix="pyiron_smoke_"); pr=Project(d); _=list(os.scandir(pr.path))
        return True,f"Project ok at {pr.path}"
    except Exception as e: return False,f"pyiron_base FAIL: {e}"

tests=[("imports",lambda:[v(m) for m in pkgs]),
       ("pyiron_base",test_pyiron_base_min),
       ("spglib",test_spglib),
       ("seekpath",test_seekpath),
       ("phonopy",test_phonopy),
       ("h5py",test_h5py),
       ("LAMMPS exec",lambda:detect_exec(["lmp","lmp_mpi","lmp_serial","lammps"])),
       ("VASP exec",lambda:detect_exec(["vasp_std","vasp_gam","vasp_ncl"]))]

fail=0
for name,t in tests:
    if name=="imports":
        for ok,msg in t():
            print(("PASS " if ok else "FAIL ")+msg); fail+=0 if ok else 1
    else:
        ok,msg=t(); print(("PASS " if ok else "SKIP " if name in ("LAMMPS exec","VASP exec") and not ok else "FAIL ")+f"{name}: {msg}")
        if name not in ("LAMMPS exec","VASP exec"): fail+=0 if ok else 1
print("\nRESULT:", "OK" if fail==0 else f"{fail} checks failed"); sys.exit(0 if fail==0 else 1)
