# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
import scanpy as sc, anndata as ad
import palantir

rng = np.random.default_rng(0)
X = rng.normal(size=(120, 50))
adata = ad.AnnData(X=X)
sc.pp.pca(adata, n_comps=20)
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=20)
sc.tl.leiden(adata, resolution=0.4)
print("Leiden categories:", adata.obs["leiden"].cat.categories.tolist())

trends = pd.DataFrame(rng.normal(size=(60, 40)), index=[f"gene_{i}" for i in range(60)], columns=np.linspace(0,1,40))
clusters = palantir.presults.cluster_gene_trends(trends, "branchA", n_neighbors=10)
print("cluster_gene_trends OK, n_clusters ~", len(clusters.unique()))
