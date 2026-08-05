import importlib
import importlib.metadata as md
import subprocess

def ver(name):
    try:
        return md.version(name)
    except Exception:
        return "not-installed"

print("Versions:")
for name in ["cellbender", "torch", "anndata", "tables", "notebook", "nbconvert"]:
    print(f"  {name}: {ver(name)}")

import cellbender
print("cellbender import OK")

from cellbender.remove_background.downstream import load_anndata_from_input_and_output
print("downstream import OK")

subprocess.run(["cellbender", "--help"], check=True, stdout=subprocess.DEVNULL)
print("cellbender --help OK")

subprocess.run(["cellbender", "remove-background", "--help"], check=True, stdout=subprocess.DEVNULL)
print("cellbender remove-background --help OK")

print("Basic CellBender smoke test passed.")