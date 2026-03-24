import numpy as np
import pandas as pd
import scanpy as sc
import tangram as tg
import torch
from scipy.sparse import csr_matrix

def dense(x):
    return x.toarray() if hasattr(x, "toarray") else np.asarray(x)

print("Versions:")
print("  tangram:", getattr(tg, "__version__", "unknown"))
print("  scanpy :", sc.__version__)
print("  torch  :", torch.__version__)
print("  cuda available:", torch.cuda.is_available())

ad_sc = sc.AnnData(
    X=csr_matrix(np.array([
        [5.0, 1.0, 0.5, 2.0],
        [4.5, 1.2, 0.4, 1.8],
        [0.3, 3.8, 4.2, 0.8],
        [0.2, 4.1, 4.0, 0.7],
    ], dtype=np.float32)),
    obs=pd.DataFrame(
        {"cluster": ["A", "A", "B", "B"]},
        index=["cell_1", "cell_2", "cell_3", "cell_4"],
    ),
    var=pd.DataFrame(index=["gene_a", "gene_b", "gene_c", "gene_extra"]),
)

ad_sp = sc.AnnData(
    X=csr_matrix(np.array([
        [4.8, 1.0, 0.6],
        [0.4, 3.9, 4.1],
    ], dtype=np.float32)),
    obs=pd.DataFrame(index=["spot_1", "spot_2"]),
    var=pd.DataFrame(index=["gene_c", "gene_b", "gene_a"]),
)

tg.pp_adatas(ad_sc, ad_sp, genes=None)

assert "training_genes" in ad_sc.uns
assert "training_genes" in ad_sp.uns
assert "overlap_genes" in ad_sc.uns
assert "overlap_genes" in ad_sp.uns

assert set(ad_sc.uns["training_genes"]) == {"gene_a", "gene_b", "gene_c"}
assert set(ad_sp.uns["training_genes"]) == {"gene_a", "gene_b", "gene_c"}
assert set(ad_sc.uns["overlap_genes"]) == {"gene_a", "gene_b", "gene_c"}
assert set(ad_sp.uns["overlap_genes"]) == {"gene_a", "gene_b", "gene_c"}

assert "rna_count_based_density" in ad_sp.obs
assert "uniform_density" in ad_sp.obs
assert np.isfinite(np.asarray(ad_sp.obs["rna_count_based_density"])).all()
assert np.isfinite(np.asarray(ad_sp.obs["uniform_density"])).all()

print("[OK] pp_adatas")

ad_map = tg.map_cells_to_space(
    adata_sc=ad_sc,
    adata_sp=ad_sp,
    device="cpu",
    mode="clusters",
    cluster_label="cluster",
    lambda_g1=1.0,
    lambda_g2=0.0,
    lambda_d=1.0,
    density_prior="uniform",
    scale=True,
    random_state=0,
    num_epochs=10,
    verbose=False,
)

map_x = dense(ad_map.X)
assert ad_map.n_obs == 2
assert ad_map.n_vars == 2
assert np.isfinite(map_x).all()
assert "training_history" in ad_map.uns
assert "main_loss" in ad_map.uns["training_history"]
assert len(ad_map.uns["training_history"]["main_loss"]) > 0

print("[OK] map_cells_to_space")

ad_ge = tg.project_genes(
    adata_map=ad_map,
    adata_sc=ad_sc,
    cluster_label="cluster",
    scale=True,
)

ge_x = dense(ad_ge.X)
assert ad_ge.n_obs == ad_sp.n_obs
assert np.isfinite(ge_x).all()
assert set(ad_ge.var_names) == set(ad_sc.var_names)

print("[OK] project_genes")
print("Tangram smoke test OK")