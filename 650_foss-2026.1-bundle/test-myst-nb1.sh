#!/usr/bin/env bash
set -euo pipefail

export PYTHONNOUSERSITE=1
export MPLBACKEND=Agg
export JUPYTER_PLATFORM_DIRS=1

expected_version="${MYST_NB_EXPECTED_VERSION:-1.4.0}"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

python -s - "${expected_version}" <<'PY'
import sys
from importlib.metadata import version
from myst_nb.core.read import is_myst_markdown_notebook, read_myst_markdown_notebook

expected = sys.argv[1]
actual = version("myst-nb")
print(f"myst-nb: {actual}")
assert actual == expected, (actual, expected)

text = """---
file_format: mystnb
kernelspec:
  name: python3
---
# Reader check

```{code-cell}
print("reader=ok")
```
"""
assert is_myst_markdown_notebook(text)
nb = read_myst_markdown_notebook(text)
assert len(nb.cells) == 2
assert nb.cells[0].cell_type == "markdown"
assert nb.cells[1].cell_type == "code"
assert "reader=ok" in nb.cells[1].source
PY

for cmd in mystnb-quickstart mystnb-to-jupyter mystnb-docutils-html sphinx-build; do
    command -v "${cmd}" >/dev/null
done

src="${workdir}/src"
out="${workdir}/build/html"
mkdir -p "${src}"

cat > "${src}/conf.py" <<'PY'
extensions = ["myst_nb"]
master_doc = "index"
project = "myst-nb EasyBuild smoke test"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
nb_execution_mode = "force"
nb_execution_timeout = 60
nb_execution_raise_on_error = True
PY

cat > "${src}/index.md" <<'EOF'
# MyST-NB smoke test

```{toctree}
:maxdepth: 1

text_nb
classic_nb
```
EOF

cat > "${src}/text_nb.md" <<'EOF'
---
file_format: mystnb
kernelspec:
  name: python3
---
# Text notebook

```{code-cell}
answer = 6 * 7
print(f"answer={answer}")
```
EOF

SRC_DIR="${src}" python -s - <<'PY'
import os
from pathlib import Path
import nbformat as nbf

src = Path(os.environ["SRC_DIR"])
nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.cells = [
    nbf.v4.new_markdown_cell("# Classic notebook"),
    nbf.v4.new_code_cell('print("classic=ok")\nvalue = 2 + 5\nvalue'),
]

with (src / "classic_nb.ipynb").open("w", encoding="utf-8") as handle:
    nbf.write(nb, handle)
PY

mystnb-to-jupyter "${src}/text_nb.md" "${workdir}/text_nb_converted.ipynb" -o

CONVERTED_NB="${workdir}/text_nb_converted.ipynb" python -s - <<'PY'
import os
import nbformat as nbf

nb = nbf.read(os.environ["CONVERTED_NB"], as_version=4)
assert len(nb.cells) == 2
assert nb.cells[1].cell_type == "code"
assert "answer = 6 * 7" in nb.cells[1].source
PY

sphinx-build -nW --keep-going -b html "${src}" "${out}"

grep -R "answer=42" "${out}/text_nb.html" >/dev/null
grep -R "classic=ok" "${out}/classic_nb.html" >/dev/null

echo "MyST-NB smoke test passed"