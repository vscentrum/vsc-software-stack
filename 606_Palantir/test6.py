# -*- coding: utf-8 -*-
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import scanpy as sc, anndata as ad, palantir

rng = np.random.default_rng(0)

n_stem=100; n_branch=100
t1 = np.linspace(0,1,n_branch); t2 = np.linspace(0,1,n_branch)
stem_t = np.linspace(0,1,n_stem)
stem = np.stack([stem_t*0, stem_t],1)
b1 = np.stack([t1, 1+t1],1)
b2 = np.stack([-t2, 1+t2],1)
coords = np.vstack([stem, b1, b2]) + rng.normal(scale=0.03, size=(n_stem+2*n_branch,2))

n_genes=200
W = rng.normal(size=(2, n_genes))
X = coords @ W + rng.normal(scale=0.4, size=(coords.shape[0], n_genes))
X = np.clip(X, 0, None)

obs = pd.DataFrame(index=[f"cell_{i}" for i in range(X.shape[0])])
var = pd.DataFrame(index=[f"gene_{j}" for j in range(X.shape[1])])
adata = ad.AnnData(X=X, obs=obs, var=var)
adata.obsm["latent2d"] = coords

palantir.preprocess.log_transform(adata)
sc.pp.pca(adata)
palantir.utils.run_diffusion_maps(adata, n_components=5)
palantir.utils.determine_multiscale_space(adata)
sc.pp.neighbors(adata); sc.tl.umap(adata)

left_arm = np.where(coords[:,0] < -0.2)[0]; right_arm = np.where(coords[:,0] > 0.2)[0]
left_tip = left_arm[np.argmax(coords[left_arm,1])]; right_tip = right_arm[np.argmax(coords[right_arm,1])]
start_cell = adata.obs_names[int(np.argmin(coords[:,1]))]
palantir.core.run_palantir(adata, start_cell, terminal_states=[adata.obs_names[left_tip], adata.obs_names[right_tip]], num_waypoints=50)

palantir.plot.plot_palantir_results(adata, s=3)
plt.savefig("palantir_matplotlib_plot_smoke.png", dpi=120, bbox_inches="tight")
print("Saved palantir_matplotlib_plot_smoke.png")
print("Fate prob shape:", np.array(adata.obsm["palantir_fate_probabilities"]).shape)
