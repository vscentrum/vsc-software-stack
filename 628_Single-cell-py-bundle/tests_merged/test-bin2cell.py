import numpy as np
import pandas as pd
from scipy import sparse
from anndata import AnnData
import bin2cell as b2c

print("bin2cell:", b2c.__version__)

X = np.array([
    [10, 0, 0],
    [5,  5, 0],
    [0,  3, 7],
    [1,  0, 1],
], dtype=np.float32)

obs = pd.DataFrame({
    "array_row": [0, 0, 1, 1],
    "array_col": [0, 1, 0, 1],
    "labels_expanded": [1, 1, 2, 0],
}, index=[f"bin{i}" for i in range(X.shape[0])])

var = pd.DataFrame(index=["g1", "g2", "g3"])

adata = AnnData(X=sparse.csr_matrix(X), obs=obs, var=var)
adata.obsm["spatial"] = np.array([
    [0.0, 0.0],
    [2.0, 0.0],
    [0.0, 2.0],
    [2.0, 2.0],
], dtype=np.float32)

adata.uns["spatial"] = {
    "synthetic": {
        "scalefactors": {
            "spot_diameter_fullres": 1.0,
        }
    }
}

adata.obs["n_counts"] = np.asarray(adata.X.sum(axis=1)).ravel()

b2c.destripe(adata, quantile=1.0, adjust_counts=True)
assert "destripe_factor" in adata.obs.columns
assert "n_counts_adjusted" in adata.obs.columns
assert np.isfinite(adata.obs["destripe_factor"]).all()
assert np.isfinite(adata.obs["n_counts_adjusted"]).all()

b2c.check_array_coordinates(adata, row_max=1, col_max=1)
assert "bin2cell" in adata.uns
assert "array_check" in adata.uns["bin2cell"]

img = b2c.grid_image(adata, "n_counts_adjusted", mpp=2)
assert isinstance(img, np.ndarray)
assert img.ndim == 2
assert img.shape[0] >= 2 and img.shape[1] >= 2
assert np.isfinite(img).all()

mask = adata.obs["labels_expanded"].to_numpy() > 0
expected_total = np.asarray(adata.X[mask].sum(axis=0)).ravel()

cdata = b2c.bin_to_cell(
    adata,
    labels_key="labels_expanded",
    spatial_keys=["spatial"],
    diameter_scale_factor=1.0,
)

assert cdata.n_obs == 2
assert "bin_count" in cdata.obs.columns
assert sorted(cdata.obs["bin_count"].astype(int).tolist()) == [1, 2]
assert "spatial" in cdata.obsm
assert cdata.obsm["spatial"].shape == (2, 2)

actual_total = np.asarray(cdata.X.sum(axis=0)).ravel()
assert np.allclose(actual_total, expected_total)

print("destriped counts:", adata.obs["n_counts_adjusted"].round(3).tolist())
print("grid image shape:", img.shape)
print("cell bin counts:", cdata.obs["bin_count"].astype(int).tolist())
print("bin2cell smoke test OK")