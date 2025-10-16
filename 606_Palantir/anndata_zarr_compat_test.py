
import os, sys, shutil, json, math
import numpy as np, pandas as pd, scipy.sparse as sp
try:
    import anndata as ad
    import zarr
except Exception as e:
    print("IMPORT_ERROR:", e); sys.exit(2)

def to_dense(x):
    if sp.issparse(x): return x.toarray()
    return np.asarray(x)

def eq(a, b, tol=1e-8):
    if type(a) != type(b):
        if isinstance(a, (list, tuple)) and isinstance(b, np.ndarray): return np.allclose(np.array(a), b, atol=tol, rtol=0)
        if isinstance(b, (list, tuple)) and isinstance(a, np.ndarray): return np.allclose(a, np.array(b), atol=tol, rtol=0)
        if sp.issparse(a) or sp.issparse(b): return np.allclose(to_dense(a), to_dense(b), atol=tol, rtol=0)
        if isinstance(a, pd.Categorical) and isinstance(b, pd.Categorical): return (a.equals(b))
    if isinstance(a, np.ndarray): return np.array_equal(a, b) or np.allclose(a, b, atol=tol, rtol=0)
    if sp.issparse(a): return np.allclose(a.toarray(), b.toarray() if sp.issparse(b) else np.asarray(b), atol=tol, rtol=0)
    if isinstance(a, pd.DataFrame): return a.equals(b)
    if isinstance(a, pd.Series): return a.equals(b)
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()): return False
        for k in a: 
            if not eq(a[k], b[k], tol): return False
        return True
    if isinstance(a, (list, tuple)):
        if len(a)!=len(b): return False
        return all(eq(x,y,tol) for x,y in zip(a,b))
    if isinstance(a, (float, np.floating)):
        if (math.isnan(a) and math.isnan(b)): return True
        return abs(float(a)-float(b))<=tol
    return a==b

def make_adata(n=11, d=7, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n,d)).astype("float32")
    X[rng.integers(0,n,size=3), rng.integers(0,d,size=3)] = 0.0
    obs = pd.DataFrame({
        "batch": pd.Categorical(rng.integers(0,3,size=n).astype(str)),
        "cell": [f"c{i}" for i in range(n)]
    }, index=[f"cell{i}" for i in range(n)])
    var = pd.DataFrame({
        "gene": [f"g{i}" for i in range(d)],
        "highly_variable": rng.random(d)>0.5
    }, index=[f"g{i}" for i in range(d)])
    layers = {"sparse": sp.csr_matrix((X*(X>0)).astype("float32"))}
    obsm = {"X_pca": rng.normal(size=(n,3)).astype("float32")}
    obsp = {"distances": sp.csr_matrix(rng.random((n,n))).astype("float32")}
    varm = {"loadings": rng.normal(size=(d,3)).astype("float32")}
    uns = {"params":{"a":1,"b":[1,2,3]}, "ref": "test"}
    adata = ad.AnnData(X=X, obs=obs, var=var, layers=layers, obsm=obsm, obsp=obsp, varm=varm, uns=uns)
    return adata

def compare_adata(a, b):
    fails=[]
    if a.n_obs!=b.n_obs or a.n_vars!=b.n_vars: fails.append("shape")
    if not eq(to_dense(a.X), to_dense(b.X)): fails.append("X")
    if not a.obs.equals(b.obs): fails.append("obs")
    if not a.var.equals(b.var): fails.append("var")
    if set(a.layers.keys())!=set(b.layers.keys()): fails.append("layers_keys")
    else:
        for k in a.layers:
            if not eq(to_dense(a.layers[k]), to_dense(b.layers[k])): fails.append(f"layers[{k}]")
    if set(a.obsm.keys())!=set(b.obsm.keys()): fails.append("obsm_keys")
    else:
        for k in a.obsm:
            if not eq(a.obsm[k], b.obsm[k]): fails.append(f"obsm[{k}]")
    if set(a.obsp.keys())!=set(b.obsp.keys()): fails.append("obsp_keys")
    else:
        for k in a.obsp:
            if not eq(to_dense(a.obsp[k]), to_dense(b.obsp[k])): fails.append(f"obsp[{k}]")
    if set(a.varm.keys())!=set(b.varm.keys()): fails.append("varm_keys")
    else:
        for k in a.varm:
            if not eq(a.varm[k], b.varm[k]): fails.append(f"varm[{k}]")
    if not eq(a.uns, b.uns): fails.append("uns")
    return fails

def main():
    print("VERSIONS", json.dumps({
        "python": sys.version.split()[0],
        "anndata": getattr(ad, "__version__", "unknown"),
        "zarr": getattr(zarr, "__version__", "unknown"),
        "pandas": pd.__version__,
        "numpy": np.__version__
    }), flush=True)
    path = "anndata_zarr_test.zarr"
    if os.path.exists(path): shutil.rmtree(path)
    a = make_adata()
    try:
        a.write_zarr(path)
        print("WRITE_ZARR_OK", path, flush=True)
    except Exception as e:
        print("WRITE_ZARR_ERROR", repr(e), flush=True); return 3
    try:
        b = ad.read_zarr(path)
        print("READ_ZARR_OK", flush=True)
    except Exception as e:
        print("READ_ZARR_ERROR", repr(e), flush=True); return 4
    fails = compare_adata(a, b)
    if fails:
        print("ROUNDTRIP_MISMATCH", ",".join(fails), flush=True); return 5
    print("SUCCESS", flush=True); return 0

if __name__=="__main__":
    code = main(); sys.exit(code)
