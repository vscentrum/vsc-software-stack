#!/usr/bin/env python3

import argparse
import hashlib
import os
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import Draw, rdDepictor, rdChemReactions
from rdkit.Chem.Draw import rdMolDraw2D


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def write_file(outdir, name, data):
    if outdir is None:
        return
    path = outdir / name
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)


def assert_svg(svg, label, min_len=1000):
    if not isinstance(svg, str):
        raise AssertionError(f"{label}: SVG output is not text: {type(svg)}")
    if len(svg) < min_len:
        raise AssertionError(f"{label}: SVG too small: {len(svg)} bytes")
    if "<svg" not in svg:
        raise AssertionError(f"{label}: no <svg> element found")
    root = ET.fromstring(svg.encode("utf-8"))
    if local_name(root.tag) != "svg":
        raise AssertionError(f"{label}: root is not svg: {root.tag}")
    counts = {}
    for elem in root.iter():
        counts[local_name(elem.tag)] = counts.get(local_name(elem.tag), 0) + 1
    drawable = sum(counts.get(k, 0) for k in ("path", "line", "polygon", "polyline", "circle", "ellipse", "rect", "text"))
    if drawable < 5:
        raise AssertionError(f"{label}: too few drawable SVG elements: {counts}")
    return counts


def make_mol(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AssertionError(f"could not parse SMILES: {smiles}")
    rdDepictor.Compute2DCoords(mol)
    return mol


def draw_svg(label, outdir, draw_func, width=500, height=350):
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    draw_func(drawer)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    counts = assert_svg(svg, label)
    digest = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:16]
    write_file(outdir, f"{label}.svg", svg)
    print(f"  {label}: svg ok, {len(svg)} bytes, sha256={digest}, elements={counts}")
    return svg


def test_basic_svg(outdir):
    mol = make_mol("CC(=O)Oc1ccccc1C(=O)O")
    draw_svg("basic_aspirin", outdir, lambda d: d.DrawMolecule(mol, legend="aspirin"))


def test_simple_highlights(outdir):
    mol = make_mol("c1ccccc1O")
    def draw(d):
        d.DrawMolecule(
            mol,
            highlightAtoms=[0, 1, 2, 6],
            highlightBonds=[0, 1],
            highlightAtomColors={0: (1.0, 0.0, 0.0), 1: (0.0, 0.7, 0.0), 2: (0.0, 0.0, 1.0), 6: (1.0, 0.6, 0.0)},
            highlightBondColors={0: (1.0, 0.0, 0.0), 1: (0.0, 0.0, 1.0)},
            highlightAtomRadii={0: 0.35, 1: 0.35, 2: 0.35, 6: 0.45},
            legend="simple highlights",
        )
    draw_svg("simple_highlights", outdir, draw)


def test_multicolour_large_highlights(outdir):
    mol = make_mol("CC(C)C1=CC=C(C=C1)C(C)C(=O)O")
    atom_colours = {
        0: [(1.0, 0.0, 0.0), (0.0, 0.0, 1.0)],
        1: [(0.0, 0.7, 0.0)],
        2: [(1.0, 0.6, 0.0)],
        3: [(0.6, 0.0, 0.8)],
        7: [(0.0, 0.7, 0.7)],
    }
    bond_colours = {
        0: [(1.0, 0.0, 0.0)],
        1: [(0.0, 0.0, 1.0)],
        4: [(0.0, 0.7, 0.0)],
    }
    radii = {0: 0.75, 1: 0.65, 2: 0.55, 3: 0.45, 7: 0.65}
    linewidths = {0: 5, 1: 5, 4: 7}
    def draw(d):
        d.DrawMoleculeWithHighlights(mol, "multi-colour large highlights", atom_colours, bond_colours, radii, linewidths)
    draw_svg("multicolour_large_highlights", outdir, draw)


def test_annotations_and_stereo(outdir):
    mol = make_mol("C[C@H](O)C(=O)O")
    mol.GetAtomWithIdx(1).SetProp("atomNote", "chiral")
    mol.GetAtomWithIdx(2).SetProp("atomNote", "OH")
    mol.GetBondWithIdx(1).SetProp("bondNote", "bond note")
    def draw(d):
        opts = d.drawOptions()
        if hasattr(opts, "addStereoAnnotation"):
            opts.addStereoAnnotation = True
        d.DrawMolecule(mol, legend="annotations and stereo")
    draw_svg("annotations_and_stereo", outdir, draw)


def test_reaction_svg(outdir):
    rxn = rdChemReactions.ReactionFromSmarts("[C:1](=[O:2])[O:3].[N:4]>>[C:1](=[O:2])[N:4]")
    if rxn is None:
        raise AssertionError("could not create reaction")
    def draw(d):
        d.DrawReaction(rxn, highlightByReactant=True)
    draw_svg("reaction", outdir, draw, width=700, height=250)


def test_grid_svg(outdir):
    mols = [make_mol(s) for s in ("c1ccccc1", "c1ccccc1O", "CC(=O)O", "CCN(CC)CC")]
    svg = Draw.MolsToGridImage(mols, molsPerRow=2, subImgSize=(250, 180), legends=["benzene", "phenol", "acetic acid", "triethylamine"], useSVG=True)
    counts = assert_svg(svg, "grid_svg", min_len=1500)
    digest = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:16]
    write_file(outdir, "grid.svg", svg)
    print(f"  grid_svg: svg ok, {len(svg)} bytes, sha256={digest}, elements={counts}")


def configure_acs1996(drawer):
    opts = drawer.drawOptions()
    for attr in ("useACS1996Mode", "acs1996Mode", "ACS1996Mode"):
        if hasattr(opts, attr):
            setattr(opts, attr, True)
            return True
    if hasattr(rdMolDraw2D, "SetACS1996Mode"):
        attempts = ((opts,), (opts, 1.0), (drawer,), (drawer, 1.0))
        for args in attempts:
            try:
                rdMolDraw2D.SetACS1996Mode(*args)
                return True
            except Exception:
                pass
    return False


def test_acs1996_mode(outdir):
    mol = make_mol("COc1ccc2nc(S(N)(=O)=O)sc2c1")
    configured = {"ok": False}
    def draw(d):
        configured["ok"] = configure_acs1996(d)
        d.DrawMolecule(mol, legend="ACS 1996 mode")
    draw_svg("acs1996_mode", outdir, draw)
    if not configured["ok"]:
        print("  acs1996_mode: ACS-specific option/function not exposed; normal SVG draw succeeded")


def test_dark_mode(outdir):
    mol = make_mol("O=C(O)c1ccccc1O")
    def draw(d):
        opts = d.drawOptions()
        if hasattr(rdMolDraw2D, "SetDarkMode"):
            rdMolDraw2D.SetDarkMode(opts)
        else:
            opts.setBackgroundColour((0.0, 0.0, 0.0))
            opts.setColourPalette({6: (0.9, 0.9, 0.9), 7: (0.3, 0.6, 1.0), 8: (1.0, 0.3, 0.3), 1: (0.8, 0.8, 0.8)})
        d.DrawMolecule(mol, legend="dark mode")
    draw_svg("dark_mode", outdir, draw)


def test_cairo_png(outdir):
    if not hasattr(rdMolDraw2D, "MolDraw2DCairo"):
        raise AssertionError("MolDraw2DCairo is not available, but Cairo support is expected")
    mol = make_mol("CC(=O)Oc1ccccc1C(=O)O")
    drawer = rdMolDraw2D.MolDraw2DCairo(500, 350)
    drawer.DrawMolecule(mol, legend="cairo aspirin")
    drawer.FinishDrawing()
    png = drawer.GetDrawingText()
    if isinstance(png, str):
        png = png.encode("latin1")
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError("Cairo output is not a PNG")
    if len(png) < 1000:
        raise AssertionError(f"Cairo PNG too small: {len(png)} bytes")
    digest = hashlib.sha256(png).hexdigest()[:16]
    write_file(outdir, "cairo_aspirin.png", png)
    print(f"  cairo_png: png ok, {len(png)} bytes, sha256={digest}")


def run(name, func, outdir):
    print(f"[RUN] {name}")
    try:
        func(outdir)
        print(f"[OK]  {name}")
        return True
    except Exception:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="rdkit_moldraw2d_outputs")
    args = parser.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Python: {sys.version.split()[0]}")
    print(f"RDKit version: {rdBase.rdkitVersion}")
    print(f"RDKit module: {Chem.__file__}")
    print(f"Output directory: {outdir}")
    print(f"MolDraw2D module: {rdMolDraw2D.__file__}")
    print(f"MolDraw2DSVG available: {hasattr(rdMolDraw2D, 'MolDraw2DSVG')}")
    print(f"MolDraw2DCairo available: {hasattr(rdMolDraw2D, 'MolDraw2DCairo')}")

    tests = [
        ("basic SVG molecule drawing", test_basic_svg),
        ("simple atom/bond highlights", test_simple_highlights),
        ("multi-colour large highlights", test_multicolour_large_highlights),
        ("atom/bond annotations and stereo labels", test_annotations_and_stereo),
        ("reaction drawing", test_reaction_svg),
        ("grid SVG drawing through Draw.MolsToGridImage", test_grid_svg),
        ("ACS 1996-style drawing path", test_acs1996_mode),
        ("dark mode drawing", test_dark_mode),
        ("Cairo PNG drawing backend", test_cairo_png),
    ]

    ok = True
    for name, func in tests:
        ok = run(name, func, outdir) and ok

    print()
    if ok:
        print("RESULT: PASS")
        print("MolDraw2D can generate valid SVG/PNG output for molecules, highlights, annotations, reactions, grid drawings, and drawing options.")
        print("This does not prove byte-for-byte equivalence with RDKit's strict SVG snapshot hashes.")
        return 0

    print("RESULT: FAIL")
    print("At least one public MolDraw2D drawing path failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())