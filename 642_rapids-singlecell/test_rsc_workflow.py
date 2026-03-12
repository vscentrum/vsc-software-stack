import numpy as np
import scipy.sparse as sp
import anndata as ad
import cupy as cp
import rapids_singlecell as rsc

def setup_rmm():
    try:
        import rmm
        from rmm.allocators.cupy import rmm_cupy_allocator
        rmm.reinitialize(managed_memory=False, pool_allocator=False, devices=0)
        cp.cuda.set_allocator(rmm_cupy_allocator)
        print("RMM allocator enabled")
    except Exception as e:
        print("RMM allocator not enabled:", repr(e))

def make_adata(n_cells=300, n_genes=1000, seed=0):
    rng = np.random.default_rng(seed)
    groups = np.repeat(np.arange(3), n_cells // 3)
    X = rng.poisson(1.0, size=(n_cells, n_genes)).astype(np.float32)
    for g in range(3):
        rows = np.where(groups == g)[0]
        cols = slice(g * 80, (g + 1) * 80)
        X[np.ix_(rows, np.arange(cols.start, cols.stop))] += rng.poisson(4.0, size=(len(rows), 80)).astype(np.float32)
    X = sp.csr_matrix(X)
    adata = ad.AnnData(X=X)
    adata.obs["group_truth"] = groups.astype(str)
    adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    return adata

def run_pca(adata, n_comps=30):
    errs = []
    for where in ("tl", "pp"):
        try:
            mod = getattr(rsc, where)
            if hasattr(mod, "pca"):
                mod.pca(adata, n_comps=n_comps)
                print(f"PCA ran via rsc.{where}.pca")
                return
        except Exception as e:
            errs.append((where, repr(e)))
    raise RuntimeError(f"PCA not available or failed in this version: {errs}")

def main():
    setup_rmm()
    adata = make_adata()
    rsc.get.anndata_to_GPU(adata)
    print("X_on_gpu_type:", type(adata.X))

    rsc.pp.normalize_total(adata, target_sum=1e4)
    rsc.pp.log1p(adata)
    rsc.pp.highly_variable_genes(adata, n_top_genes=300, flavor="cell_ranger")
    assert "highly_variable" in adata.var.columns
    assert int(np.asarray(adata.var["highly_variable"]).sum()) > 0

    rsc.pp.filter_highly_variable(adata)
    assert adata.n_vars <= 300

    rsc.pp.scale(adata, max_value=10)
    run_pca(adata, n_comps=30)

    assert "X_pca" in adata.obsm
    assert adata.obsm["X_pca"].shape == (adata.n_obs, 30)

    rsc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)
    assert "connectivities" in adata.obsp
    assert "distances" in adata.obsp

    rsc.tl.umap(adata)
    assert "X_umap" in adata.obsm
    assert adata.obsm["X_umap"].shape == (adata.n_obs, 2)

    rsc.tl.leiden(adata, resolution=0.5)
    assert "leiden" in adata.obs
    n_clusters = int(adata.obs["leiden"].nunique())
    assert 1 < n_clusters < adata.n_obs, f"Unexpected number of clusters: {n_clusters}"

    umap = adata.obsm["X_umap"]
    if hasattr(umap, "get"):
        umap = umap.get()
    assert np.isfinite(np.asarray(umap)).all()

    print("cells:", adata.n_obs)
    print("genes_after_hvg:", adata.n_vars)
    print("clusters:", n_clusters)
    print("OK: rapids_singlecell GPU workflow works")

if __name__ == "__main__":
    main()