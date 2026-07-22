#!/usr/bin/env python

import math
import sys
import tempfile
import traceback
from copy import deepcopy
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from pathlib import Path


def check_dist(name, expected=None):
    try:
        found = version(name)
    except PackageNotFoundError as err:
        raise RuntimeError(f"Missing distribution: {name}") from err

    if expected is not None and found != expected:
        raise RuntimeError(f"{name}: expected {expected}, got {found}")

    print(f"{name}: {found}")


def run_test(name, function):
    print(f"\n=== {name} ===")

    try:
        function()
    except Exception:
        print(f"FAILED: {name}", file=sys.stderr)
        traceback.print_exc()
        raise

    print(f"PASSED: {name}")


def assert_same_molecule(reference, candidate):
    assert candidate.n_atoms == reference.n_atoms
    assert candidate.n_bonds == reference.n_bonds
    assert candidate.to_smiles(isomeric=True) == reference.to_smiles(isomeric=True)


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
    "bson": "0.5.10",
}

state = {}


def test_metadata():
    assert sys.version_info[:2] == (3, 14), sys.version

    print(f"Python: {sys.version.split()[0]}")

    for name, expected in expected_versions.items():
        check_dist(name, expected)

    for name in [
        "openmm",
        "rdkit",
        "pydantic",
        "Pint",
        "networkx",
        "MDTraj",
        "PyYAML",
        "xmltodict",
        "cachetools",
        "python-constraint",
    ]:
        check_dist(name)


def test_imports():
    import bson
    import constraint
    import mdtraj
    import networkx
    import openff.amber_ff_ports
    import openff.packmol
    import openff.utilities
    import openforcefields
    import openmm
    import pyedr
    import rdkit
    import xmltodict
    import yaml
    from openff.interchange import Interchange
    from openff.interchange.components.mdconfig import MDConfig
    from openff.interchange.models import TopologyKey
    from openff.toolkit import ForceField, Molecule, Topology
    from openff.toolkit.utils import RDKitToolkitWrapper
    from openff.units import Quantity, unit

    state.update(
        {
            "bson": bson,
            "ForceField": ForceField,
            "Interchange": Interchange,
            "MDConfig": MDConfig,
            "Molecule": Molecule,
            "Quantity": Quantity,
            "RDKitToolkitWrapper": RDKitToolkitWrapper,
            "Topology": Topology,
            "TopologyKey": TopologyKey,
            "openmm": openmm,
            "unit": unit,
        }
    )


def test_optional_components():
    try:
        import openff.nagl
    except ModuleNotFoundError:
        print("OpenFF NAGL is not installed, as expected")
    else:
        raise RuntimeError("openff.nagl is unexpectedly importable")

    from openff.toolkit import GLOBAL_TOOLKIT_REGISTRY
    from openff.toolkit.utils import AmberToolsToolkitWrapper

    if AmberToolsToolkitWrapper.is_available():
        print("AmberTools is visible in the current environment but is not used")
    else:
        assert not any(
            isinstance(toolkit, AmberToolsToolkitWrapper)
            for toolkit in GLOBAL_TOOLKIT_REGISTRY.registered_toolkits
        )
        print("AmberTools is unavailable and absent from the registry, as expected")


def test_bson():
    bson = state["bson"]

    original = {
        "name": "ethanol",
        "atoms": 9,
        "values": [1, 2, 3],
    }

    restored = bson.loads(bson.dumps(original))
    assert restored == original


def test_units_and_pydantic():
    from pydantic import BaseModel

    Quantity = state["Quantity"]
    unit = state["unit"]

    class QuantityModel(BaseModel):
        value: Quantity

    length = 1.0 * unit.nanometer

    assert math.isclose(
        length.m_as(unit.angstrom),
        10.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    )

    model = QuantityModel(value=length)
    schema = QuantityModel.model_json_schema()
    encoded = model.model_dump_json()
    decoded = QuantityModel.model_validate_json(encoded)

    assert "properties" in schema
    assert math.isclose(
        decoded.value.m_as(unit.nanometer),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def test_rdkit_molecule():
    from rdkit import Chem

    Molecule = state["Molecule"]
    RDKitToolkitWrapper = state["RDKitToolkitWrapper"]

    toolkit = RDKitToolkitWrapper()
    molecule = Molecule.from_smiles(
        "CCO",
        toolkit_registry=toolkit,
    )

    molecule.generate_conformers(
        n_conformers=2,
        toolkit_registry=toolkit,
    )

    assert molecule.n_atoms == 9
    assert molecule.n_bonds == 8
    assert molecule.n_conformers >= 1

    rdkit_molecule = molecule.to_rdkit()
    assert Chem.MolToSmiles(Chem.RemoveHs(rdkit_molecule)) == "CCO"

    smiles = molecule.to_smiles(toolkit_registry=toolkit)
    inchi = molecule.to_inchi(toolkit_registry=toolkit)
    inchikey = molecule.to_inchikey(toolkit_registry=toolkit)

    assert smiles
    assert inchi.startswith("InChI=")
    assert len(inchikey) == 27

    restored = Molecule.from_rdkit(rdkit_molecule)
    assert_same_molecule(molecule, restored)

    state["molecule"] = molecule
    state["rdkit_toolkit"] = toolkit


def test_partial_charges():
    molecule = state["molecule"]
    toolkit = state["rdkit_toolkit"]
    unit = state["unit"]

    gasteiger = deepcopy(molecule)
    gasteiger.assign_partial_charges(
        partial_charge_method="gasteiger",
        toolkit_registry=toolkit,
    )

    assert gasteiger.partial_charges is not None
    assert len(gasteiger.partial_charges) == gasteiger.n_atoms
    assert abs(
        gasteiger.total_charge.m_as(unit.elementary_charge)
    ) < 1e-6

    mmff94 = deepcopy(molecule)
    mmff94.assign_partial_charges(
        partial_charge_method="mmff94",
        toolkit_registry=toolkit,
    )

    assert mmff94.partial_charges is not None
    assert len(mmff94.partial_charges) == mmff94.n_atoms
    assert abs(
        mmff94.total_charge.m_as(unit.elementary_charge)
    ) < 1e-6

    state["charged_molecule"] = gasteiger


def test_serialization():
    Molecule = state["Molecule"]
    molecule = state["charged_molecule"]

    round_trips = {
        "JSON": (
            molecule.to_json,
            Molecule.from_json,
        ),
        "YAML": (
            molecule.to_yaml,
            Molecule.from_yaml,
        ),
        "BSON": (
            molecule.to_bson,
            Molecule.from_bson,
        ),
        "MessagePack": (
            molecule.to_messagepack,
            Molecule.from_messagepack,
        ),
        "pickle": (
            molecule.to_pickle,
            Molecule.from_pickle,
        ),
    }

    for name, methods in round_trips.items():
        serializer, deserializer = methods
        restored = deserializer(serializer())

        assert_same_molecule(molecule, restored)
        assert restored.partial_charges is not None

        print(f"{name} round-trip OK")

    print("XML round-trip skipped: Molecule.from_xml() is not implemented")

    with tempfile.TemporaryDirectory() as tmpdir:
        sdf_path = Path(tmpdir) / "ethanol.sdf"

        molecule.to_file(
            sdf_path,
            file_format="SDF",
        )

        restored = Molecule.from_file(
            sdf_path,
            file_format="SDF",
        )

        assert_same_molecule(molecule, restored)
        assert restored.n_conformers >= 1

        print("SDF round-trip OK")


def test_force_fields():
    from openff.toolkit.typing.engines.smirnoff.forcefield import (
        get_available_force_fields,
    )

    ForceField = state["ForceField"]
    Topology = state["Topology"]
    molecule = state["charged_molecule"]

    force_field = ForceField("openff-2.2.1.offxml")
    topology = Topology.from_molecules([molecule])
    labels = force_field.label_molecules(topology)

    assert force_field.registered_parameter_handlers
    assert len(labels) == 1
    assert labels[0]
    assert "Bonds" in labels[0]
    assert "vdW" in labels[0]

    print(
        "OpenFF 2.2.1 labeling OK: "
        f"{len(force_field.registered_parameter_handlers)} handlers"
    )

    available = set(get_available_force_fields())

    amber_candidates = sorted(
        name
        for name in available
        if name.startswith("ff14sb_off_impropers_")
    )

    assert amber_candidates, (
        "No ff14sb_off_impropers force fields were discovered from "
        "openff-amber-ff-ports"
    )

    preferred = "ff14sb_off_impropers_0.0.4.offxml"

    if preferred in amber_candidates:
        amber_name = preferred
    else:
        amber_name = amber_candidates[-1]

    amber_force_field = ForceField(amber_name)

    assert amber_force_field.registered_parameter_handlers
    assert "Bonds" in amber_force_field.registered_parameter_handlers
    assert "ImproperTorsions" in amber_force_field.registered_parameter_handlers
    assert "vdW" in amber_force_field.registered_parameter_handlers

    print(f"Amber FF port loaded successfully: {amber_name}")

    state["force_field"] = force_field
    state["topology"] = topology


def test_interchange():
    Interchange = state["Interchange"]
    molecule = state["charged_molecule"]
    force_field = state["force_field"]
    topology = state["topology"]

    interchange = Interchange.from_smirnoff(
        force_field=force_field,
        topology=topology,
        charge_from_molecules=[molecule],
    )

    assert interchange.topology.n_molecules == 1
    assert interchange.topology.n_atoms == molecule.n_atoms
    assert interchange.collections
    assert "Bonds" in interchange.collections
    assert "Electrostatics" in interchange.collections
    assert "vdW" in interchange.collections

    state["interchange"] = interchange


def test_openmm_export():
    molecule = state["charged_molecule"]
    force_field = state["force_field"]
    topology = state["topology"]
    interchange = state["interchange"]

    direct_system = force_field.create_openmm_system(
        topology,
        charge_from_molecules=[molecule],
    )

    interchange_system = interchange.to_openmm()

    assert direct_system.getNumParticles() == molecule.n_atoms
    assert interchange_system.getNumParticles() == molecule.n_atoms
    assert direct_system.getNumForces() > 0
    assert interchange_system.getNumForces() > 0

    state["openmm_system"] = interchange_system


def test_openmm_energy():
    openmm = state["openmm"]
    molecule = state["charged_molecule"]
    system = state["openmm_system"]

    from openff.units.openmm import to_openmm
    from openmm import unit as openmm_unit

    positions = to_openmm(molecule.conformers[0])

    integrator = openmm.VerletIntegrator(
        1.0 * openmm_unit.femtosecond
    )

    platform = openmm.Platform.getPlatformByName("Reference")
    context = openmm.Context(
        system,
        integrator,
        platform,
    )

    try:
        context.setPositions(positions)

        result = context.getState(
            getEnergy=True,
            getForces=True,
        )

        energy = result.getPotentialEnergy().value_in_unit(
            openmm_unit.kilojoule_per_mole
        )

        forces = result.getForces(asNumpy=True)

        assert math.isfinite(energy)
        assert forces.shape == (molecule.n_atoms, 3)

        print(
            "Reference-platform potential energy: "
            f"{energy:.6f} kJ/mol"
        )
    finally:
        del context
        del integrator


def test_models_and_configuration():
    MDConfig = state["MDConfig"]
    TopologyKey = state["TopologyKey"]
    interchange = state["interchange"]

    key = TopologyKey(atom_indices=(0,))
    config = MDConfig.from_interchange(interchange)

    assert key.atom_indices == (0,)
    assert isinstance(config.periodic, bool)

    print(f"MDConfig periodic: {config.periodic}")


tests = [
    (
        "installed package metadata",
        test_metadata,
    ),
    (
        "imports",
        test_imports,
    ),
    (
        "excluded optional components",
        test_optional_components,
    ),
    (
        "BSON",
        test_bson,
    ),
    (
        "OpenFF Units and Pydantic",
        test_units_and_pydantic,
    ),
    (
        "RDKit molecule operations",
        test_rdkit_molecule,
    ),
    (
        "RDKit partial charges",
        test_partial_charges,
    ),
    (
        "serialization and SDF I/O",
        test_serialization,
    ),
    (
        "force-field loading and labeling",
        test_force_fields,
    ),
    (
        "Interchange construction",
        test_interchange,
    ),
    (
        "OpenMM system export",
        test_openmm_export,
    ),
    (
        "OpenMM energy and force evaluation",
        test_openmm_energy,
    ),
    (
        "Interchange models and MDConfig",
        test_models_and_configuration,
    ),
]

for test_name, test_function in tests:
    run_test(
        test_name,
        test_function,
    )

print(
    "\nAll OpenFF Toolkit tests passed without using "
    "AmberTools or OpenFF NAGL."
)