import os, pandas as pd, scanpy as sc, palantir, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data_dir = os.path.abspath(".")
url = "https://dp-lab-data-public.s3.amazonaws.com/palantir/marrow_sample_scseq_counts.h5ad"
fn = os.path.join(data_dir, "marrow_sample_scseq_counts.h5ad")
ad = sc.read(fn, backup_url=url)

# optional: basic normalization
palantir.preprocess.log_transform(ad)

sc.pp.highly_variable_genes(ad, n_top_genes=1500, flavor="cell_ranger")
sc.pp.pca(ad)

palantir.utils.run_diffusion_maps(ad, n_components=5)
palantir.utils.determine_multiscale_space(ad)

sc.pp.neighbors(ad); sc.tl.umap(ad)

start_cell = ad.obs_names[0]
_ = palantir.core.run_palantir(ad, start_cell, num_waypoints=300)

palantir.plot.plot_palantir_results(ad, s=3)
plt.savefig("palantir_results_umap.png", dpi=150, bbox_inches="tight")
print("Saved palantir_results_umap.png")

palantir.plot.plot_diffusion_components(ad)
plt.savefig("palantir_diffusion_components.png", dpi=150, bbox_inches="tight")
print("Saved palantir_diffusion_components.png")
