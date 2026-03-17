import cellrank as cr
print("cellrank", cr.__version__)
print("PseudotimeKernel:", cr.kernels.PseudotimeKernel)
print("GPCCA:", cr.estimators.GPCCA)
print("GAM:", cr.models.GAM)
print("OK")

import numpy as np
import scanpy as sc
from anndata import AnnData

rs = np.random.RandomState(0)
adata = AnnData(rs.normal(size=(80, 20)).astype("float32"))

sc.pp.pca(adata, n_comps=10)
sc.pp.neighbors(adata, n_neighbors=10)

adata.obs["pt"] = np.linspace(0.0, 1.0, adata.n_obs)

k = cr.kernels.PseudotimeKernel(adata, time_key="pt")
k.compute_transition_matrix()
assert k.transition_matrix.shape == (adata.n_obs, adata.n_obs)

g = cr.estimators.GPCCA(k)
g.compute_schur(n_components=5)
g.compute_macrostates(n_states=3, n_cells=10)

assert g.macrostates is not None
print("CellRank kernel + GPCCA OK")