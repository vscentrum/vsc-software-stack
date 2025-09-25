# test3-iodata.py

import importlib, pkgutil, numpy as np, pytest

def test_iodata_api_available():
    io = importlib.import_module("iodata")
    assert hasattr(io, "load_one") and hasattr(io, "dump_one")

def test_iodata_roundtrip_xyz(tmp_path):
    from iodata import IOData, load_one, dump_one
    R = np.array([[0.000,0.000,0.000],[0.000,0.000,0.9572],[0.9266,0.000,-0.2396]])
    Z = np.array([8,1,1])
    mol = IOData(atnums=Z, atcoords=R, title="H2O")  # no charge; XYZ doesn't preserve it
    fn = tmp_path / "water.xyz"
    dump_one(mol, str(fn))
    mol2 = load_one(str(fn))
    np.testing.assert_allclose(mol2.atcoords, R, atol=1e-6)
    assert (mol2.atnums == Z).all()

def test_pyiron_gpl_imports_clean():
    pkg = importlib.import_module("pyiron_gpl")
    bad=[]
    for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try: importlib.import_module(m.name)
        except Exception as e: bad.append((m.name, repr(e)))
    assert not bad, "Import failures:\n" + "\n".join(f"- {n}: {e}" for n,e in bad)

def test_bridge_to_pyiron_atomistics():
    from iodata import IOData
    try:
        from pyiron_atomistics.atomistics.structure.atoms import Atoms
    except Exception:
        from pyiron.atomistics.structure.atoms import Atoms
    R = np.array([[0.0,0.0,0.0],[0.0,0.0,0.74]])
    Z = np.array([1,1])
    a = Atoms(numbers=Z.tolist(), positions=R)
    assert a.get_number_of_atoms() == 2
    assert a.positions.shape == (2,3)
