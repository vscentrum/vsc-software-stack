#!/usr/bin/env python -s

from importlib.metadata import PackageNotFoundError, version

def check_dist(name, expected=None):
    try:
        found = version(name)
    except PackageNotFoundError:
        raise RuntimeError(f"missing distribution: {name}")
    if expected is not None and found != expected:
        raise RuntimeError(f"{name}: expected {expected}, got {found}")
    print(f"{name}: {found}")

expected_versions = {
    "openff-toolkit": "0.18.1",
    "openff-interchange": "0.5.3",
    "openff-packmol": "0.1",
    "openff-units": "0.4.0",
    "openff-utilities": "0.1.16",
    "openff-amber-ff-ports": "2025.9.0",
    "openforcefields": "2026.1.0",
    "pyedr": "0.8.0",
    "mda-xdrlib": "0.2.0",
}

print("Checking installed package metadata")
for name, expected in expected_versions.items():
    check_dist(name, expected)

for name in ["openmm", "rdkit", "pydantic", "Pint", "networkx", "MDTraj"]:
    check_dist(name)

print("\nChecking imports")
from openff.toolkit import ForceField, Molecule, Topology
from openff.toolkit.utils import RDKitToolkitWrapper
from openff.units import unit
from openff.interchange import Interchange
from openff.interchange.components.mdconfig import MDConfig
from openff.interchange.models import TopologyKey
from rdkit import Chem
import openmm
import openforcefields
import openff.amber_ff_ports
import openff.packmol
import openff.utilities
import pyedr

print("Imports OK")

print("\nChecking optional components are absent or non-required")
try:
    import openff.nagl
except ModuleNotFoundError:
    print("openff.nagl not installed, OK for this temporary base build")
else:
    raise RuntimeError("openff.nagl unexpectedly importable; update this test if NAGL is added")

print("\nChecking AmberTools availability")
try:
    from openff.toolkit.utils import AmberToolsToolkitWrapper
    amber = AmberToolsToolkitWrapper()
    print(f"AmberToolsToolkitWrapper usable: {amber}")
except Exception as err:
    print(f"AmberTools unavailable, OK for this temporary base build: {type(err).__name__}: {err}")

print("\nChecking RDKit-backed molecule creation")
mol = Molecule.from_smiles("CCO", toolkit_registry=RDKitToolkitWrapper())
mol.generate_conformers(n_conformers=1, toolkit_registry=RDKitToolkitWrapper())
assert mol.n_atoms == 9
assert mol.n_conformers == 1
rdmol = mol.to_rdkit()
assert Chem.MolToSmiles(Chem.RemoveHs(rdmol)) == "CCO"
print(f"Molecule OK: {mol.to_smiles()} with {mol.n_atoms} atoms")

print("\nChecking OpenFF units")
length = 1.0 * unit.nanometer
assert abs(length.m_as(unit.angstrom) - 10.0) < 1e-12
print("Units OK")

print("\nChecking force field loading")
ff = ForceField("openff-2.2.1.offxml")
topology = Topology.from_molecules([mol])
print(f"ForceField OK: {len(ff.registered_parameter_handlers)} parameter handlers")

print("\nChecking OpenFF Interchange construction without AmberTools AM1-BCC")
mol.assign_partial_charges(
    partial_charge_method="gasteiger",
    toolkit_registry=RDKitToolkitWrapper(),
)
assert mol.partial_charges is not None

interchange = Interchange.from_smirnoff(
    force_field=ff,
    topology=topology,
    charge_from_molecules=[mol],
)
assert interchange.topology.n_molecules == 1
assert interchange.topology.n_atoms == 9
print("Interchange OK with RDKit/Gasteiger preassigned charges")

print("\nChecking OpenMM export")
omm_system = interchange.to_openmm()
assert omm_system.getNumParticles() == 9
print(f"OpenMM System OK: {omm_system.getNumParticles()} particles")

print("\nChecking small model/config classes")
key = TopologyKey(atom_indices=(0,))
cfg = MDConfig.from_interchange(interchange)
assert key.atom_indices == (0,)
print(f"MDConfig OK: periodic={cfg.periodic}")

print("\nOpenFF Toolkit temporary base smoke test passed")