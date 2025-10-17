import numpy as np, pandas as pd
import scanpy as sc
import anndata as ad
import palantir

rng = np.random.default_rng(42)

# synthetic Y-shaped manifold in 2D latent space
n_stem=150; n_branch=150
t1 = np.linspace(0,1,n_branch); t2 = np.linspace(0,1,n_branch)
stem_t = np.linspace(0,1,n_stem)
stem = np.stack([stem_t*0, stem_t],1)
b1 = np.stack([t1, 1+t1],1)
b2 = np.stack([-t2, 1+t2],1)
coords = np.vstack([stem, b1, b2])
coords += rng.normal(scale=0.03, size=coords.shape)

# project to genes with random weights to get an expression matrix
n_genes=300
W = rng.normal(size=(coords.shape[1], n_genes))
X = coords @ W + rng.normal(scale=0.5, size=(coords.shape[0], n_genes))
X = np.clip(X, a_min=0, a_max=None)

obs = pd.DataFrame(index=[f"cell_{i}" for i in range(X.shape[0])])
var = pd.DataFrame(index=[f"gene_{j}" for j in range(X.shape[1])])

adata = ad.AnnData(X=X, obs=obs, var=var)
adata.obsm["latent2d"] = coords

# minimal Palantir preprocessing
palantir.preprocess.log_transform(adata)
sc.pp.pca(adata)

# diffusion maps + multiscale
palantir.utils.run_diffusion_maps(adata, n_components=5)
palantir.utils.determine_multiscale_space(adata)

# pick a start cell at the root of the Y (lowest y on stem)
start_idx = int(np.argmin(coords[:,1]))
start_cell = adata.obs_names[start_idx]

# choose two terminal cells explicitly from the two arms:
left_arm = np.where(coords[:,0] < -0.2)[0]
right_arm = np.where(coords[:,0] > 0.2)[0]
left_tip = left_arm[np.argmax(coords[left_arm,1])]
right_tip = right_arm[np.argmax(coords[right_arm,1])]
terminal_states = [adata.obs_names[left_tip], adata.obs_names[right_tip]]

pr = palantir.core.run_palantir(adata, start_cell, terminal_states=terminal_states, num_waypoints=50)

required_obs = ["palantir_pseudotime", "palantir_entropy"]
required_obsm = ["palantir_fate_probabilities"]
missing = {"obs":[k for k in required_obs if k not in adata.obs],
           "obsm":[k for k in required_obsm if k not in adata.obsm]}

assert not missing["obs"] and not missing["obsm"], f"Missing keys: {missing}"

print("OK: Palantir ran on synthetic data.")
print({k: float(adata.obs[k].min()) for k in required_obs} | {k: float(adata.obs[k].max()) for k in required_obs})
print("Fate prob shape:", np.array(adata.obsm["palantir_fate_probabilities"]).shape)
