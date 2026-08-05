import tempfile, pathlib, subprocess, json

td = pathlib.Path(tempfile.mkdtemp())
nb = td / "tiny.ipynb"

nb.write_text(json.dumps({
    "cells": [
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["print('ok')"]
        }
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5
}))

subprocess.run([
    "jupyter", "nbconvert",
    "--ExecutePreprocessor.timeout=60",
    "--to", "notebook",
    "--allow-errors",
    "--execute",
    str(nb)
], cwd=td, check=True)

subprocess.run([
    "jupyter", "nbconvert",
    "--to", "html",
    "--TemplateExporter.exclude_input=True",
    str(td / "tiny.nbconvert.ipynb")
], cwd=td, check=True)

assert (td / "tiny.nbconvert.html").is_file()
print("nbconvert execute+html OK")