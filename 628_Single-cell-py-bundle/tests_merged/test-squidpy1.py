import numpy as np
import pandas as pd
import anndata as ad
import squidpy as sq
import scanpy as sc
import spatialdata
import spatialdata_plot
import xrspatial
import pims
import dask_image
import datashader
import ome_zarr
import matplotlib
matplotlib.use("Agg")

# print("scanpy", sc.__version__)
# print("squidpy", sq.__version__)
# print("spatialdata", spatialdata.__version__)
# print("numpy", np.__version__)

# 1) Synthetic smoke test: imports + graph/statistics only
n = 60
rng = np.random.default_rng(0)
X = rng.poisson(1.0, size=(n, 20)).astype(np.float32)

obs = pd.DataFrame(
    {
        "cluster": pd.Categorical(
            np.where(np.arange(n) % 3 == 0, "A", np.where(np.arange(n) % 3 == 1, "B", "C"))
        )
    },
    index=[f"cell{i}" for i in range(n)],
)
var = pd.DataFrame(index=[f"gene{i}" for i in range(X.shape[1])])

adata_syn = ad.AnnData(X=X, obs=obs, var=var)
side = int(np.ceil(np.sqrt(n)))
adata_syn.obsm["spatial"] = np.array([(i % side, i // side) for i in range(n)], dtype=float)

sq.gr.spatial_neighbors(adata_syn, coord_type="generic", delaunay=True)
sq.gr.nhood_enrichment(adata_syn, cluster_key="cluster", n_perms=10, seed=0)
sq.gr.spatial_autocorr(adata_syn, mode="moran", genes=adata_syn.var_names[:5], n_perms=10)

assert "spatial_connectivities" in adata_syn.obsp
assert "spatial_distances" in adata_syn.obsp
assert "cluster_nhood_enrichment" in adata_syn.uns
assert "moranI" in adata_syn.uns

print("Synthetic graph/statistics test: OK")

# 2) Real Squidpy dataset test: plotting + image features
adata = sq.datasets.visium_hne_adata()
img = sq.datasets.visium_hne_image()

print("dataset adata shape:", adata.shape)
print("dataset image shape:", img.shape)

adata = adata[:200].copy()

sq.gr.spatial_neighbors(adata)
sq.gr.nhood_enrichment(adata, cluster_key="cluster", n_perms=10, seed=0)
sq.gr.spatial_autocorr(adata, mode="moran", genes=adata.var_names[:10], n_perms=10)

sq.im.calculate_image_features(
    adata,
    img,
    features="summary",
    key_added="img_features",
    n_jobs=1,
    scale=1.0,
)

sq.pl.spatial_scatter(adata, color="cluster", save="_dataset_cluster.png")
sq.pl.nhood_enrichment(adata, cluster_key="cluster", save="_dataset_nhood.png")

assert "spatial_connectivities" in adata.obsp
assert "cluster_nhood_enrichment" in adata.uns
assert "moranI" in adata.uns
assert "img_features" in adata.obsm or "img_features" in adata.uns

feat = adata.obsm["img_features"] if "img_features" in adata.obsm else adata.uns["img_features"]

print("feature object type:", type(feat))
if isinstance(feat, pd.DataFrame):
    print("feature shape:", feat.shape)

print("Dataset plotting/image-features test: OK")
print("ALL OK")