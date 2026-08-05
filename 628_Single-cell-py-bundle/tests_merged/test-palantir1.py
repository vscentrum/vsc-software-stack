#!/usr/bin/env python3
import os
import warnings
import pandas as pd
import scanpy as sc
import palantir
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from numba.core.errors import NumbaDeprecationWarning
    warnings.filterwarnings("ignore", category=NumbaDeprecationWarning)
except Exception:
    pass

outdir = "palantir_test"
os.makedirs(outdir, exist_ok=True)

file_path = os.path.join(outdir, "marrow_sample_scseq_counts.h5ad")
download_url = "https://dp-lab-data-public.s3.amazonaws.com/palantir/marrow_sample_scseq_counts.h5ad"

print("palantir version:", getattr(palantir, "__version__", "unknown"))
print("scanpy version:", sc.__version__)

ad = sc.read(file_path, backup_url=download_url)

try:
    sc.pp.normalize_per_cell(ad)
except AttributeError:
    sc.pp.normalize_total(ad)

palantir.preprocess.log_transform(ad)
sc.pp.highly_variable_genes(ad, n_top_genes=1500, flavor="cell_ranger")
sc.pp.pca(ad)

palantir.utils.run_diffusion_maps(ad, n_components=5)
palantir.utils.determine_multiscale_space(ad)

sc.pp.neighbors(ad)
sc.tl.umap(ad)

terminal_states = pd.Series(
    ["DC", "Mono", "Ery"],
    index=[
        "Run5_131097901611291",
        "Run5_134936662236454",
        "Run4_200562869397916",
    ],
)
start_cell = "Run5_164698952452459"

res = palantir.core.run_palantir(
    ad,
    start_cell,
    num_waypoints=500,
    terminal_states=terminal_states,
)

assert res is not None
assert "palantir_pseudotime" in ad.obs
assert "palantir_entropy" in ad.obs
assert "palantir_fate_probabilities" in ad.obsm
assert "palantir_waypoints" in ad.uns

fp = ad.obsm["palantir_fate_probabilities"]
assert len(res.pseudotime) == ad.n_obs
assert len(res.entropy) == ad.n_obs
assert fp.shape[0] == ad.n_obs

palantir.plot.plot_palantir_results(ad, s=3)
plt.savefig(os.path.join(outdir, "palantir_results.png"), dpi=150, bbox_inches="tight")
plt.close("all")

ad.write(os.path.join(outdir, "palantir_results.h5ad"))

print("OK")