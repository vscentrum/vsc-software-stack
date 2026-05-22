#!/usr/bin/env python3

import importlib
import importlib.metadata as md
import os
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import zipfile
from pathlib import Path


EXPECTED = {
    "hatchling": "1.29.0",
    "pathspec": "1.1.1",
    "pluggy": "1.6.0",
    "calver": "2025.10.20",
    "trove-classifiers": "2026.1.14.14",
    "hatch-vcs": "0.5.0",
    "hatch-fancy-pypi-readme": "25.1.0",
    "hatch-requirements-txt": "0.4.1",
    "hatch-docstring-description": "1.1.1",
}

IMPORTS = [
    "hatchling",
    "pathspec",
    "pluggy",
    "calver",
    "trove_classifiers",
    "hatch_vcs",
    "hatch_fancy_pypi_readme",
    "hatch_requirements_txt",
    "hatch_docstring_description",
]

PLUGIN_DISTS = [
    "hatch-vcs",
    "hatch-fancy-pypi-readme",
    "hatch-requirements-txt",
    "hatch-docstring-description",
]


def run(cmd, cwd=None):
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(p.stdout)
    if p.returncode != 0:
        raise RuntimeError(f"command failed with exit code {p.returncode}: {' '.join(cmd)}")
    return p.stdout


def check_versions():
    print("== Installed versions ==")
    for dist, expected in EXPECTED.items():
        got = md.version(dist)
        print(f"{dist}: {got}")
        if got != expected:
            raise RuntimeError(f"{dist}: expected {expected}, got {got}")


def check_imports():
    print("\n== Imports ==")
    for mod in IMPORTS:
        importlib.import_module(mod)
        print(f"[OK] import {mod}")


def check_plugin_entry_points():
    print("\n== Hatchling plugin entry points ==")
    for dist_name in PLUGIN_DISTS:
        dist = md.distribution(dist_name)
        eps = list(dist.entry_points)
        if not eps:
            raise RuntimeError(f"{dist_name} has no entry points")
        for ep in eps:
            obj = ep.load()
            print(f"[OK] {dist_name}: {ep.group}:{ep.name} -> {obj}")


def check_cli():
    print("\n== CLI ==")
    run(["hatchling", "--help"])
    out = run([
        sys.executable,
        "-c",
        "import importlib.metadata as md; print(md.version('hatchling'))",
    ])
    if out.strip() != "1.29.0":
        raise RuntimeError(f"wrong hatchling version from metadata: {out.strip()}")
    print("[OK] hatchling executable works")


def write_project(root):
    pkg = root / "src" / "eb_hatchling_smoketest"
    pkg.mkdir(parents=True)

    (root / "README.md").write_text("# Hatchling smoke test\n", encoding="utf-8")
    (pkg / "__init__.py").write_text(
        "def answer():\n    return 42\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(textwrap.dedent("""
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        name = "eb-hatchling-smoketest"
        version = "0.1.0"
        description = "EasyBuild Hatchling smoke test"
        readme = "README.md"
        requires-python = ">=3.11"
        license = "MIT"
        classifiers = [
            "Programming Language :: Python :: 3",
        ]

        [tool.hatch.build.targets.wheel]
        packages = ["src/eb_hatchling_smoketest"]
    """).strip() + "\n", encoding="utf-8")


def check_build():
    print("\n== Build wheel and sdist ==")
    with tempfile.TemporaryDirectory(prefix="hatchling-smoke-") as td:
        root = Path(td)
        write_project(root)

        run(["hatchling", "build"], cwd=root)

        dist = root / "dist"
        wheels = sorted(dist.glob("*.whl"))
        sdists = sorted(dist.glob("*.tar.gz"))

        if len(wheels) != 1:
            raise RuntimeError(f"expected exactly one wheel, found {wheels}")
        if len(sdists) != 1:
            raise RuntimeError(f"expected exactly one sdist, found {sdists}")

        wheel = wheels[0]
        sdist = sdists[0]
        print(f"[OK] wheel created: {wheel.name}")
        print(f"[OK] sdist created: {sdist.name}")

        with zipfile.ZipFile(wheel) as zf:
            names = zf.namelist()
            required = [
                "eb_hatchling_smoketest/__init__.py",
                "eb_hatchling_smoketest-0.1.0.dist-info/METADATA",
                "eb_hatchling_smoketest-0.1.0.dist-info/WHEEL",
            ]
            for item in required:
                if item not in names:
                    raise RuntimeError(f"missing from wheel: {item}")
                print(f"[OK] wheel contains {item}")

        with tarfile.open(sdist, "r:gz") as tf:
            names = tf.getnames()
            expected = "eb_hatchling_smoketest-0.1.0/pyproject.toml"
            if expected not in names:
                raise RuntimeError(f"missing from sdist: {expected}")
            print(f"[OK] sdist contains {expected}")

        sys.path.insert(0, str(wheel))
        try:
            mod = importlib.import_module("eb_hatchling_smoketest")
            if mod.answer() != 42:
                raise RuntimeError("import from built wheel returned wrong result")
            print("[OK] import from built wheel works")
        finally:
            sys.path.pop(0)


def main():
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    check_versions()
    check_imports()
    check_plugin_entry_points()
    check_cli()
    check_build()
    print("\nAll Hatchling smoke tests passed.")


if __name__ == "__main__":
    main()