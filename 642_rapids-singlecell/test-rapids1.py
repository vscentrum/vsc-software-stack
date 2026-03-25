import numpy as np
import cupy as cp
import cudf
import cugraph
from cuml.decomposition import PCA
from cuml.neighbors import NearestNeighbors

def main():
    gdf = cudf.DataFrame({"a": [1, 1, 2, 2], "b": [10, 20, 30, 40]})
    out = gdf.groupby("a").b.sum().sort_index()
    assert out.to_pandas().tolist() == [30, 70]

    rs = cp.random.RandomState(0)
    X = rs.normal(0, 1, (256, 32), dtype=cp.float32)
    pca = PCA(n_components=8, random_state=0)
    X_pca = pca.fit_transform(X)
    assert X_pca.shape == (256, 8)
    assert cp.isfinite(X_pca).all()

    nn = NearestNeighbors(n_neighbors=5)
    nn.fit(X_pca)
    dists, inds = nn.kneighbors(X_pca[:16])
    assert dists.shape == (16, 5)
    assert inds.shape == (16, 5)
    assert cp.isfinite(dists).all()

    edges = cudf.DataFrame({"src": [0, 1, 2, 3, 4], "dst": [1, 2, 0, 4, 3]})
    G = cugraph.Graph(directed=False)
    G.from_cudf_edgelist(edges, source="src", destination="dst")
    cc = cugraph.connected_components(G)
    n_components = int(cc["labels"].nunique())
    assert n_components == 2, f"Expected 2 components, got {n_components}"

    print("OK: cudf/cuml/cugraph basic functionality works")

if __name__ == "__main__":
    main()