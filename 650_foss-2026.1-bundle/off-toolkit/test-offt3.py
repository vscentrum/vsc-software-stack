#!/usr/bin/env python

import argparse
import math
import shutil
import sys
import tempfile
import traceback
import warnings
from copy import deepcopy
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np


EXPECTED_VERSIONS = {
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

EXPECTED_AMBERTOOLS_VERSION = "26.1"
STATE = {}
RESULTS = []


def check_dist(name, expected=None):
    try:
        found = version(name)
    except PackageNotFoundError as err:
        raise RuntimeError(f"missing distribution: {name}") from err
    if expected is not None and found != expected:
        raise RuntimeError(f"{name}: expected {expected}, got {found}")
    print(f"{name}: {found}")
    return found


def assert_finite_quantity(values):
    array = np.asarray(values.magnitude, dtype=float)
    assert np.all(np.isfinite(array))


def assert_same_molecule(reference, candidate):
    from openff.toolkit import Molecule

    same, atom_map = Molecule.are_isomorphic(
        reference,
        candidate,
        return_atom_map=True,
    )
    assert same
    assert atom_map is not None
    assert reference.n_atoms == candidate.n_atoms
    assert reference.n_bonds == candidate.n_bonds


def one_molecule(value):
    if isinstance(value, list):
        assert len(value) == 1
        return value[0]
    return value


def run_test(name, function, skip=False, skip_reason=""):
    print(f"\n=== {name} ===")
    if skip:
        print(f"SKIPPED: {skip_reason}")
        RESULTS.append((name, "SKIPPED", skip_reason))
        return

    try:
        function()
    except Exception as err:
        print(f"FAILED: {name}", file=sys.stderr)
        traceback.print_exc()
        RESULTS.append((name, "FAILED", f"{type(err).__name__}: {err}"))
    else:
        print(f"PASSED: {name}")
        RESULTS.append((name, "PASSED", ""))


def test_metadata_and_imports():
    assert sys.version_info[:2] == (3, 14), sys.version
    print(f"Python: {sys.version.split()[0]}")

    for name, expected in EXPECTED_VERSIONS.items():
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
    from openff.toolkit.utils import AmberToolsToolkitWrapper, RDKitToolkitWrapper
    from openff.units import Quantity, unit

    STATE.update(
        {
            "AmberToolsToolkitWrapper": AmberToolsToolkitWrapper,
            "ForceField": ForceField,
            "Interchange": Interchange,
            "MDConfig": MDConfig,
            "Molecule": Molecule,
            "Quantity": Quantity,
            "RDKitToolkitWrapper": RDKitToolkitWrapper,
            "Topology": Topology,
            "TopologyKey": TopologyKey,
            "bson": bson,
            "mdtraj": mdtraj,
            "openmm": openmm,
            "unit": unit,
        }
    )


def test_toolkit_registry():
    from openff.toolkit import GLOBAL_TOOLKIT_REGISTRY

    RDKitToolkitWrapper = STATE["RDKitToolkitWrapper"]
    AmberToolsToolkitWrapper = STATE["AmberToolsToolkitWrapper"]

    assert RDKitToolkitWrapper.is_available()
    assert AmberToolsToolkitWrapper.is_available()

    rdkit = RDKitToolkitWrapper()
    amber = AmberToolsToolkitWrapper()

    registered = GLOBAL_TOOLKIT_REGISTRY.registered_toolkits
    assert any(isinstance(toolkit, RDKitToolkitWrapper) for toolkit in registered)
    assert any(isinstance(toolkit, AmberToolsToolkitWrapper) for toolkit in registered)

    names = [toolkit.toolkit_name for toolkit in registered]
    print(f"Global toolkit registry: {names}")
    print(f"RDKit wrapper version: {rdkit.toolkit_version}")
    print(f"AmberTools wrapper version: {amber.toolkit_version}")

    assert str(amber.toolkit_version).startswith(EXPECTED_AMBERTOOLS_VERSION)
    assert set(amber.supported_charge_methods) == {
        "am1bcc",
        "am1-mulliken",
        "gasteiger",
    }

    for executable in ("antechamber", "sqm"):
        path = shutil.which(executable)
        assert path is not None, f"{executable} not found on PATH"
        print(f"{executable}: {path}")

    try:
        import openff.nagl
    except ModuleNotFoundError:
        print("OpenFF NAGL is not installed, as expected for this EC")
    else:
        print("OpenFF NAGL is importable; it is not exercised by this script")

    STATE["rdkit"] = rdkit
    STATE["amber"] = amber


def test_units_and_pydantic():
    from pydantic import BaseModel

    Quantity = STATE["Quantity"]
    unit = STATE["unit"]

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


def test_bson_package():
    bson = STATE["bson"]
    payload = {
        "name": "ethanol",
        "atoms": 9,
        "values": [1, 2, 3],
    }
    assert bson.loads(bson.dumps(payload)) == payload


def test_rdkit_molecule_core():
    from rdkit import Chem

    Molecule = STATE["Molecule"]
    rdkit = STATE["rdkit"]

    molecule = Molecule.from_smiles(
        "CCO",
        toolkit_registry=rdkit,
        name="ethanol",
    )
    molecule.generate_conformers(
        n_conformers=3,
        rms_cutoff=0.1 * STATE["unit"].angstrom,
        toolkit_registry=rdkit,
    )

    assert molecule.n_atoms == 9
    assert molecule.n_bonds == 8
    assert molecule.n_conformers >= 1
    assert molecule.hill_formula == "C2H6O"
    assert molecule.total_charge.m_as(STATE["unit"].elementary_charge) == 0

    smiles = molecule.to_smiles(
        explicit_hydrogens=False,
        toolkit_registry=rdkit,
    )
    mapped_smiles = molecule.to_smiles(
        explicit_hydrogens=True,
        mapped=True,
        toolkit_registry=rdkit,
    )
    inchi = molecule.to_inchi(toolkit_registry=rdkit)
    inchikey = molecule.to_inchikey(toolkit_registry=rdkit)

    assert smiles
    assert mapped_smiles
    assert inchi.startswith("InChI=")
    assert len(inchikey) == 27

    from_inchi = Molecule.from_inchi(inchi, toolkit_registry=rdkit)
    from_mapped = Molecule.from_mapped_smiles(
        mapped_smiles,
        toolkit_registry=rdkit,
    )
    from_rdkit = Molecule.from_rdkit(molecule.to_rdkit())

    assert_same_molecule(molecule, from_inchi)
    assert_same_molecule(molecule, from_mapped)
    assert_same_molecule(molecule, from_rdkit)

    rdkit_molecule = molecule.to_rdkit()
    assert Chem.MolToSmiles(Chem.RemoveHs(rdkit_molecule)) == "CCO"

    graph = molecule.to_networkx()
    assert graph.number_of_nodes() == molecule.n_atoms
    assert graph.number_of_edges() == molecule.n_bonds

    matches = molecule.chemical_environment_matches(
        "[#6:1]-[#8:2]",
        unique=True,
        toolkit_registry=rdkit,
    )
    assert len(matches) == 1

    canonical = molecule.canonical_order_atoms(toolkit_registry=rdkit)
    assert_same_molecule(molecule, canonical)

    mapping = {index: molecule.n_atoms - index - 1 for index in range(molecule.n_atoms)}
    remapped = molecule.remap(mapping, current_to_new=True)
    assert_same_molecule(molecule, remapped)

    same, atom_map = Molecule.are_isomorphic(
        molecule,
        remapped,
        return_atom_map=True,
    )
    assert same
    assert atom_map is not None
    assert len(atom_map) == molecule.n_atoms

    assert molecule.ordered_connection_table_hash()
    STATE["molecule"] = molecule


def test_rdkit_enumeration_and_bonds():
    Molecule = STATE["Molecule"]
    rdkit = STATE["rdkit"]

    stereo = Molecule.from_smiles(
        "CC(F)Cl",
        toolkit_registry=rdkit,
        allow_undefined_stereo=True,
    )
    stereoisomers = stereo.enumerate_stereoisomers(
        undefined_only=True,
        max_isomers=4,
        toolkit_registry=rdkit,
    )
    assert len(stereoisomers) >= 2
    assert all(isinstance(item, Molecule) for item in stereoisomers)
    print(f"Stereoisomers generated: {len(stereoisomers)}")

    tautomer_source = Molecule.from_smiles(
        "CC(=O)CC(=O)C",
        toolkit_registry=rdkit,
    )
    tautomers = tautomer_source.enumerate_tautomers(
        max_states=20,
        toolkit_registry=rdkit,
    )
    assert isinstance(tautomers, list)
    assert all(isinstance(item, Molecule) for item in tautomers)
    print(f"Alternative tautomers generated: {len(tautomers)}")

    butane = Molecule.from_smiles("CCCC", toolkit_registry=rdkit)
    rotatable = butane.find_rotatable_bonds(toolkit_registry=rdkit)
    assert len(rotatable) >= 1
    assert len(list(butane.nth_degree_neighbors(1))) == butane.n_bonds


def test_rdkit_partial_charges():
    rdkit = STATE["rdkit"]
    unit = STATE["unit"]

    for method in ("gasteiger", "mmff94"):
        molecule = deepcopy(STATE["molecule"])
        molecule.assign_partial_charges(
            partial_charge_method=method,
            toolkit_registry=rdkit,
        )
        assert molecule.partial_charges is not None
        assert len(molecule.partial_charges) == molecule.n_atoms
        assert_finite_quantity(molecule.partial_charges)
        assert abs(
            molecule.partial_charges.sum().m_as(unit.elementary_charge)
        ) < 1e-6
        print(f"RDKit {method} charges OK")


def test_molecule_serialization_and_file_io():
    Molecule = STATE["Molecule"]
    rdkit = STATE["rdkit"]
    molecule = deepcopy(STATE["molecule"])

    molecule.assign_partial_charges(
        partial_charge_method="gasteiger",
        toolkit_registry=rdkit,
    )

    restored = Molecule.from_dict(molecule.to_dict())
    assert_same_molecule(molecule, restored)
    assert restored.partial_charges is not None
    print("dict round-trip OK")

    round_trips = {
        "JSON": (molecule.to_json, Molecule.from_json),
        "YAML": (molecule.to_yaml, Molecule.from_yaml),
        "BSON": (molecule.to_bson, Molecule.from_bson),
        "MessagePack": (molecule.to_messagepack, Molecule.from_messagepack),
        "pickle": (molecule.to_pickle, Molecule.from_pickle),
    }

    for name, (serializer, deserializer) in round_trips.items():
        restored = deserializer(serializer())
        assert_same_molecule(molecule, restored)
        assert restored.partial_charges is not None
        print(f"{name} round-trip OK")

    print("XML skipped: Molecule.from_xml() is not implemented in 0.18.1")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        for file_format, suffix in (
            ("SDF", ".sdf"),
            ("MOL", ".mol"),
            ("SMI", ".smi"),
        ):
            path = root / f"ethanol{suffix}"
            molecule.to_file(
                str(path),
                file_format=file_format,
                toolkit_registry=rdkit,
            )
            loaded = one_molecule(
                Molecule.from_file(
                    str(path),
                    file_format=file_format,
                    toolkit_registry=rdkit,
                )
            )
            assert_same_molecule(molecule, loaded)
            print(f"{file_format} file round-trip OK")

        pdb_path = root / "ethanol.pdb"
        molecule.to_file(
            str(pdb_path),
            file_format="PDB",
            toolkit_registry=rdkit,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            loaded_pdb = Molecule.from_pdb_and_smiles(
                str(pdb_path),
                molecule.to_smiles(
                    explicit_hydrogens=False,
                    toolkit_registry=rdkit,
                ),
            )
        assert_same_molecule(molecule, loaded_pdb)
        assert loaded_pdb.n_conformers == 1
        print("PDB plus SMILES round-trip OK")

        xyz_path = root / "ethanol.xyz"
        molecule.to_file(str(xyz_path), file_format="XYZ")
        assert xyz_path.is_file()
        assert xyz_path.stat().st_size > 0
        print("XYZ writing OK")


def test_topology_operations():
    Molecule = STATE["Molecule"]
    Topology = STATE["Topology"]
    Quantity = STATE["Quantity"]
    unit = STATE["unit"]
    rdkit = STATE["rdkit"]
    mdtraj = STATE["mdtraj"]

    ethanol = deepcopy(STATE["molecule"])
    water = Molecule.from_smiles("O", toolkit_registry=rdkit)

    topology = Topology.from_molecules([ethanol, deepcopy(ethanol), water])
    assert topology.n_molecules == 3
    assert topology.n_unique_molecules == 2
    assert topology.n_atoms == 21
    assert topology.n_bonds == 18

    topology_copy = Topology.from_dict(topology.to_dict())
    assert topology_copy.n_molecules == topology.n_molecules
    assert topology_copy.n_atoms == topology.n_atoms

    single = Topology.from_molecules([ethanol])
    single.set_positions(ethanol.conformers[0])
    positions = single.get_positions()
    assert positions.shape == (ethanol.n_atoms, 3)

    periodic = Topology(single)
    periodic.box_vectors = Quantity(np.eye(3) * 3.0, unit.nanometer)
    assert periodic.is_periodic
    assert periodic.box_vectors.shape == (3, 3)

    openmm_topology = single.to_openmm()
    assert openmm_topology.getNumAtoms() == ethanol.n_atoms
    assert openmm_topology.getNumBonds() == ethanol.n_bonds

    from_openmm = Topology.from_openmm(
        openmm_topology,
        unique_molecules=[ethanol],
        positions=positions,
    )
    assert from_openmm.n_atoms == ethanol.n_atoms
    assert from_openmm.n_bonds == ethanol.n_bonds
    assert from_openmm.get_positions().shape == positions.shape

    mdtraj_topology = mdtraj.Topology.from_openmm(openmm_topology)
    from_mdtraj = Topology.from_mdtraj(
        mdtraj_topology,
        unique_molecules=[ethanol],
        positions=positions,
    )
    assert from_mdtraj.n_atoms == ethanol.n_atoms
    assert from_mdtraj.n_bonds == ethanol.n_bonds

    STATE["topology"] = single


def test_ambertools_charge_methods():
    amber = STATE["amber"]
    unit = STATE["unit"]

    charged = {}

    for method in ("gasteiger", "am1-mulliken", "am1bcc"):
        molecule = deepcopy(STATE["molecule"])
        molecule.assign_partial_charges(
            partial_charge_method=method,
            toolkit_registry=amber,
        )
        assert molecule.partial_charges is not None
        assert len(molecule.partial_charges) == molecule.n_atoms
        assert_finite_quantity(molecule.partial_charges)
        total = molecule.partial_charges.sum().m_as(unit.elementary_charge)
        assert abs(total) < 1e-6
        charged[method] = molecule
        print(f"AmberTools {method} charges OK; total charge={total:.12f} e")

    STATE["am1bcc_molecule"] = charged["am1bcc"]


def test_ambertools_fractional_bond_orders():
    amber = STATE["amber"]
    molecule = deepcopy(STATE["molecule"])

    molecule.assign_fractional_bond_orders(
        bond_order_model="am1-wiberg",
        toolkit_registry=amber,
    )

    values = []
    for bond in molecule.bonds:
        value = bond.fractional_bond_order
        assert value is not None
        assert math.isfinite(float(value))
        assert float(value) > 0.0
        values.append(float(value))

    assert len(values) == molecule.n_bonds
    print(
        "AM1-Wiberg bond-order range: "
        f"{min(values):.6f} to {max(values):.6f}"
    )


def test_force_fields_and_labeling():
    from openff.toolkit.typing.engines.smirnoff.forcefield import get_available_force_fields

    ForceField = STATE["ForceField"]
    topology = STATE["topology"]

    available = set(get_available_force_fields())
    assert "openff-2.2.1.offxml" in available
    assert "ff14sb_off_impropers_0.0.4.offxml" in available

    force_field = ForceField("openff-2.2.1.offxml")
    assert force_field.registered_parameter_handlers
    assert force_field.get_parameter_handler("Bonds")
    assert force_field.get_parameter_handler("Angles")
    assert force_field.get_parameter_handler("ProperTorsions")
    assert force_field.get_parameter_handler("vdW")
    assert force_field.get_parameter_handler("Electrostatics")

    labels = force_field.label_molecules(topology)
    assert len(labels) == 1
    assert labels[0]
    for handler in ("Bonds", "Angles", "ProperTorsions", "vdW"):
        assert handler in labels[0]

    amber_port = ForceField("ff14sb_off_impropers_0.0.4.offxml")
    assert "ImproperTorsions" in amber_port.registered_parameter_handlers
    assert "vdW" in amber_port.registered_parameter_handlers

    print(f"OpenFF handlers: {force_field.registered_parameter_handlers}")
    STATE["force_field"] = force_field


def test_force_field_ambertools_integration():
    force_field = STATE["force_field"]
    topology = STATE["topology"]

    system = force_field.create_openmm_system(topology)

    assert system.getNumParticles() == topology.n_atoms
    assert system.getNumForces() > 0
    print(
        "ForceField.create_openmm_system completed through "
        "ToolkitAM1BCC with the global AmberTools registry"
    )

    STATE["direct_system"] = system


def test_interchange_and_openmm():
    Interchange = STATE["Interchange"]
    molecule = STATE["am1bcc_molecule"]
    force_field = STATE["force_field"]
    Topology = STATE["Topology"]
    openmm = STATE["openmm"]

    topology = Topology.from_molecules([molecule])
    interchange = Interchange.from_smirnoff(
        force_field=force_field,
        topology=topology,
        charge_from_molecules=[molecule],
    )

    assert interchange.topology.n_molecules == 1
    assert interchange.topology.n_atoms == molecule.n_atoms
    for collection in ("Bonds", "Angles", "ProperTorsions", "Electrostatics", "vdW"):
        assert collection in interchange.collections

    system = interchange.to_openmm()
    assert system.getNumParticles() == molecule.n_atoms
    assert system.getNumForces() > 0

    from openff.units.openmm import to_openmm
    from openmm import unit as openmm_unit

    positions = to_openmm(molecule.conformers[0])
    integrator = openmm.VerletIntegrator(1.0 * openmm_unit.femtosecond)
    platform = openmm.Platform.getPlatformByName("Reference")
    context = openmm.Context(system, integrator, platform)

    try:
        context.setPositions(positions)
        context_state = context.getState(getEnergy=True, getForces=True)
        energy = context_state.getPotentialEnergy().value_in_unit(
            openmm_unit.kilojoule_per_mole
        )
        forces = context_state.getForces(asNumpy=True)
        assert math.isfinite(energy)
        force_values = forces.value_in_unit(
            openmm_unit.kilojoule_per_mole / openmm_unit.nanometer
        )
        assert force_values.shape == (molecule.n_atoms, 3)
        assert np.all(np.isfinite(np.asarray(force_values)))
        print(f"Reference potential energy: {energy:.6f} kJ/mol")
    finally:
        del context
        del integrator

    STATE["interchange"] = interchange


def test_interchange_models():
    MDConfig = STATE["MDConfig"]
    TopologyKey = STATE["TopologyKey"]
    interchange = STATE["interchange"]

    key = TopologyKey(atom_indices=(0,))
    config = MDConfig.from_interchange(interchange)

    assert key.atom_indices == (0,)
    assert isinstance(config.periodic, bool)
    print(f"MDConfig periodic: {config.periodic}")


def print_summary():
    print("\n=== summary ===")
    for name, status, detail in RESULTS:
        suffix = f" - {detail}" if detail else ""
        print(f"{status:7s} {name}{suffix}")

    failed = [result for result in RESULTS if result[1] == "FAILED"]
    skipped = [result for result in RESULTS if result[1] == "SKIPPED"]
    passed = [result for result in RESULTS if result[1] == "PASSED"]

    print(
        f"\nPassed: {len(passed)}; failed: {len(failed)}; "
        f"skipped: {len(skipped)}"
    )

    if failed:
        raise SystemExit(1)

    print(
        "\nAll selected OpenFF Toolkit 0.18.1 functional tests passed, "
        "including AmberTools integration."
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Comprehensive functional test for OpenFF Toolkit 0.18.1 "
            "with RDKit, AmberTools, Interchange, and OpenMM."
        )
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Skip the slower AmberTools AM1 charge, Wiberg bond-order, "
            "and automatic ToolkitAM1BCC integration tests."
        ),
    )
    args = parser.parse_args()

    tests = [
        ("package metadata and imports", test_metadata_and_imports, False, ""),
        ("toolkit registry and executables", test_toolkit_registry, False, ""),
        ("OpenFF Units and Pydantic", test_units_and_pydantic, False, ""),
        ("BSON package", test_bson_package, False, ""),
        ("RDKit molecule core API", test_rdkit_molecule_core, False, ""),
        (
            "RDKit stereochemistry, tautomers, and bonds",
            test_rdkit_enumeration_and_bonds,
            False,
            "",
        ),
        ("RDKit partial charges", test_rdkit_partial_charges, False, ""),
        (
            "molecule serialization and file I/O",
            test_molecule_serialization_and_file_io,
            False,
            "",
        ),
        ("topology operations and conversions", test_topology_operations, False, ""),
        (
            "AmberTools partial-charge methods",
            test_ambertools_charge_methods,
            args.quick,
            "--quick requested",
        ),
        (
            "AmberTools AM1-Wiberg bond orders",
            test_ambertools_fractional_bond_orders,
            args.quick,
            "--quick requested",
        ),
        ("force fields and parameter labeling", test_force_fields_and_labeling, False, ""),
        (
            "ForceField automatic AmberTools integration",
            test_force_field_ambertools_integration,
            args.quick,
            "--quick requested",
        ),
        (
            "Interchange and OpenMM energy evaluation",
            test_interchange_and_openmm,
            args.quick,
            "requires the AM1-BCC molecule produced by the full test",
        ),
        (
            "Interchange model classes",
            test_interchange_models,
            args.quick,
            "requires the Interchange object produced by the full test",
        ),
    ]

    for name, function, skip, reason in tests:
        run_test(name, function, skip=skip, skip_reason=reason)

    print_summary()


if __name__ == "__main__":
    main()
