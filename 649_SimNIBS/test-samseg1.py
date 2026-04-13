#!/usr/bin/env python3
import importlib
import pathlib
import pkgutil
import sys

print("Python:", sys.version)

mods = [
    "samseg",
    "samseg.gems",
    "samseg.gems.gemsbindings",
]

loaded = {}
for name in mods:
    mod = importlib.import_module(name)
    loaded[name] = mod
    print(f"[OK] import {name}: {getattr(mod, '__file__', '<namespace>')}")

samseg = loaded["samseg"]
pkg_path = pathlib.Path(samseg.__file__).resolve().parent
print("samseg package dir:", pkg_path)

assert pkg_path.is_dir(), "samseg package directory not found"

# Confirm compiled extension is present and importable
gemsbindings = loaded["samseg.gems.gemsbindings"]
ext_path = pathlib.Path(gemsbindings.__file__).resolve()
print("gemsbindings extension:", ext_path)
assert ext_path.exists(), "gemsbindings extension file does not exist"
assert ext_path.suffix in {".so", ".pyd", ".dylib"}, f"unexpected extension suffix: {ext_path.suffix}"

# List direct samseg submodules/packages to confirm packaging is sane
submods = sorted(m.name for m in pkgutil.iter_modules([str(pkg_path)]))
print("samseg direct submodules:", ", ".join(submods[:30]))
assert "gems" in submods, "samseg.gems package not found"

# Basic version probe if available
version = getattr(samseg, "__version__", None)
print("samseg version:", version if version is not None else "<not exposed>")

print("\nSAMSEG smoke test passed")