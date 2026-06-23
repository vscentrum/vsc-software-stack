#!/usr/bin/env python3

from rdkit import Chem, rdBase
from rdkit.Chem import rdCIPLabeler

print(f"RDKit version: {rdBase.rdkitVersion}")
print(f"rdCIPLabeler module: {rdCIPLabeler.__file__}")

def check_atom_cip(smiles, atom_idx, expected):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AssertionError(f"Could not parse SMILES: {smiles}")

    rdCIPLabeler.AssignCIPLabels(mol)

    atom = mol.GetAtomWithIdx(atom_idx)
    if not atom.HasProp("_CIPCode"):
        raise AssertionError(f"{smiles}: atom {atom_idx} has no _CIPCode")

    got = atom.GetProp("_CIPCode")
    if got != expected:
        raise AssertionError(f"{smiles}: atom {atom_idx} expected {expected}, got {got}")

    print(f"OK atom CIP: {smiles} atom {atom_idx} = {got}")

def check_bond_cip(smiles, bond_idx, expected):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AssertionError(f"Could not parse SMILES: {smiles}")

    rdCIPLabeler.AssignCIPLabels(mol)

    bond = mol.GetBondWithIdx(bond_idx)
    if not bond.HasProp("_CIPCode"):
        raise AssertionError(f"{smiles}: bond {bond_idx} has no _CIPCode")

    got = bond.GetProp("_CIPCode")
    if got != expected:
        raise AssertionError(f"{smiles}: bond {bond_idx} expected {expected}, got {got}")

    print(f"OK bond CIP: {smiles} bond {bond_idx} = {got}")

# Tetrahedral R/S labels
check_atom_cip("C[C@H](O)C(=O)O", 1, "S")
check_atom_cip("C[C@@H](O)C(=O)O", 1, "R")

# Another simple tetrahedral stereocentre
check_atom_cip("F[C@](Cl)(Br)I", 1, "S")
check_atom_cip("F[C@@](Cl)(Br)I", 1, "R")

# E/Z double-bond labels
check_bond_cip("C/C=C/C", 1, "E")
check_bond_cip("C/C=C\\C", 1, "Z")

print("RESULT: PASS")
print("rdCIPLabeler.AssignCIPLabels assigns expected _CIPCode values for representative R/S and E/Z cases.")