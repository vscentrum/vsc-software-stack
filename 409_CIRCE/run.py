import numpy as np
import circe as ci
import scanpy as sc
import scipy as sp

atac = sc.datasets.blobs(n_centers=10, n_variables=2_000, n_observations=300, random_state=0)
atac.X = np.random.poisson(lam=2, size=atac.X.shape)
cell_names = [f"cell_{i}" for i in range(1, atac.shape[0]+1)]
# number of chr_start_end region names
region_names = [[f"chr{i}_{str(j)}_{str(j+150)}"
                 for j in range(1, 10000*400+1, 10000)]
                for i in range(1, 6)]
regions_names = [item for sublist in region_names for item in sublist]
atac.var_names = regions_names
atac.obs_names = cell_names

sc.pp.filter_genes(atac, min_cells=1)
sc.pp.filter_cells(atac, min_genes=1)
atac

atac = ci.add_region_infos(atac)

metacells = ci.metacells.compute_metacells(atac)

ci.compute_atac_network(
    atac, #metacells,
    organism="human",
)
atac.varp["atac_network"]

window_size = 100_000
distance_constraint=50_000
s = 0.85
ci.compute_atac_network(
    atac, #metacells,
    window_size=window_size,
    s=s,
    distance_constraint=distance_constraint,
    unit_distance = 1000,
    n_samples=50,
    n_samples_maxtry=100,
    max_alpha_iteration=100
)

atac.X = sp.sparse.csr_matrix(atac.X)
# atac.X = atac.X.toarray()

final_score = ci.sliding_graphical_lasso(
    atac,
    n_samples=50,
    n_samples_maxtry=100,
    max_alpha_iteration=500,
    verbose=True
)
atac.varp['atac_network'] = final_score

circe_network = ci.extract_atac_links(atac) #metacells)
circe_network.head(3)

subset_atac = ci.subset_region(atac, "chr1", 10_000, 200_000)

circe_network_subset = ci.extract_atac_links(subset_atac)
circe_network_subset.head(3)

ci.plot_connections(
    circe_network,
    chromosome="chr1",
    start=10_000,
    end=200_000,
    sep=("_","_"),
    abs_threshold=0.01
)

ccans = ci.find_ccans(circe_network, seed=0)
ccans.head(3)

atac = ci.add_ccans(atac)
atac.var.head()

ccans = ci.find_ccans(circe_network, seed=0, coaccess_cutoff_override=1e-7)

atac.var[atac.var['CCAN']==2].head(3)

atac.var['CCAN'].value_counts().head()

ccan_number = atac.var['CCAN'].value_counts().index[0]

ci.draw.plot_ccan(
    atac,
    ccan_module=ccan_number,
    sep=('_', '_'),
    abs_threshold=0,
    figsize=(15,5),
    only_positive=True)
