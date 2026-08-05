import os
import shutil
import numpy as np
import pandas as pd
import torch
import anndata as ad
import scarches as sca

def ok(msg):
    print(f"[OK] {msg}")

def fail(msg):
    raise RuntimeError(msg)

print("Versions:")
print("  scArches :", getattr(sca, "__version__", "unknown"))
print("  PyTorch  :", torch.__version__)
print("  CUDA build:", torch.version.cuda)
print("  CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("  CUDA device count:", torch.cuda.device_count())
    print("  CUDA device 0:", torch.cuda.get_device_name(0))
else:
    print("  CUDA device 0: <none visible>")

np.random.seed(0)
torch.manual_seed(0)

n_ref = 160
n_query = 80
n_genes = 64
n_latent = 5

genes = [f"gene_{i:03d}" for i in range(n_genes)]
rng = np.random.default_rng(0)

base_means = rng.uniform(1.0, 4.0, size=n_genes)
type_effect_a = rng.normal(0.0, 0.6, size=n_genes)
type_effect_b = rng.normal(0.0, 0.6, size=n_genes)
batch_effect_ref0 = rng.normal(0.0, 0.3, size=n_genes)
batch_effect_ref1 = rng.normal(0.0, 0.3, size=n_genes)
batch_effect_query = rng.normal(0.0, 0.3, size=n_genes)

def make_counts(n, batch_name, type_names):
    xs = []
    obs = []
    for i in range(n):
        ct = type_names[i % len(type_names)]
        if ct == "A":
            mu = np.exp(np.log(base_means) + type_effect_a)
        else:
            mu = np.exp(np.log(base_means) + type_effect_b)

        if batch_name == "ref0":
            mu = mu * np.exp(batch_effect_ref0)
        elif batch_name == "ref1":
            mu = mu * np.exp(batch_effect_ref1)
        elif batch_name == "query0":
            mu = mu * np.exp(batch_effect_query)

        libsize = rng.uniform(0.8, 1.2)
        lam = np.clip(mu * libsize, 0.05, 50.0)
        x = rng.poisson(lam).astype(np.float32)
        xs.append(x)
        obs.append((batch_name, ct))
    obs = pd.DataFrame(obs, columns=["batch", "cell_type"])
    return np.vstack(xs), obs

x_ref0, obs_ref0 = make_counts(n_ref // 2, "ref0", ["A", "B"])
x_ref1, obs_ref1 = make_counts(n_ref // 2, "ref1", ["A", "B"])
x_query, obs_query = make_counts(n_query, "query0", ["A", "B"])

x_ref = np.vstack([x_ref0, x_ref1])
obs_ref = pd.concat([obs_ref0, obs_ref1], ignore_index=True)

adata_ref = ad.AnnData(
    X=x_ref,
    obs=obs_ref,
    var=pd.DataFrame(index=genes),
)
adata_query = ad.AnnData(
    X=x_query,
    obs=obs_query,
    var=pd.DataFrame(index=genes),
)

adata_ref.obs_names = [f"ref_{i}" for i in range(adata_ref.n_obs)]
adata_query.obs_names = [f"query_{i}" for i in range(adata_query.n_obs)]

if adata_ref.X.min() < 0:
    fail("Reference data are not counts.")
if adata_query.X.min() < 0:
    fail("Query data are not counts.")
ok("Synthetic count AnnData objects created")

accelerator = "gpu" if torch.cuda.is_available() else "cpu"
devices = 1

sca.models.SCVI.setup_anndata(adata_ref, batch_key="batch")
ok("SCVI.setup_anndata on reference data")

model = sca.models.SCVI(
    adata_ref,
    n_latent=n_latent,
    n_layers=2,
    gene_likelihood="nb",
)

model.train(max_epochs=12, accelerator=accelerator, devices=devices)
ok(f"Reference model trained with accelerator={accelerator}, devices={devices}")

z_ref = model.get_latent_representation()
if z_ref.shape != (adata_ref.n_obs, n_latent):
    fail(f"Unexpected reference latent shape: {z_ref.shape}")
ok(f"Reference latent shape = {z_ref.shape}")

norm_ref = model.get_normalized_expression()
norm_ref_arr = np.asarray(norm_ref)
if norm_ref_arr.shape != (adata_ref.n_obs, adata_ref.n_vars):
    fail(f"Unexpected normalized expression shape: {norm_ref_arr.shape}")
ok(f"Normalized expression shape = {norm_ref_arr.shape}")

if not getattr(model, "is_trained", False):
    fail("Model reports is_trained=False after training.")
ok("Model reports is_trained=True")

ref_dir = "scarches_smoketest_ref"
if os.path.exists(ref_dir):
    shutil.rmtree(ref_dir)

model.save(ref_dir, overwrite=True, save_anndata=False)
if not os.path.isdir(ref_dir):
    fail("Reference model directory was not created.")
ok(f"Reference model saved to {ref_dir}")

loaded = sca.models.SCVI.load(ref_dir, adata=adata_ref)
z_loaded = loaded.get_latent_representation()
if z_loaded.shape != z_ref.shape:
    fail("Loaded model latent shape differs from original model.")
ok("Saved model reloaded successfully")

adata_query_prepped = adata_query.copy()
sca.models.SCVI.prepare_query_anndata(adata_query_prepped, ref_dir)
ok("Query AnnData prepared against reference model")

query_model = sca.models.SCVI.load_query_data(
    adata_query_prepped,
    ref_dir,
    freeze_dropout=True,
)

query_model.train(
    max_epochs=6,
    accelerator=accelerator,
    devices=devices,
    plan_kwargs={"weight_decay": 0.0},
)
ok(f"Query model trained with accelerator={accelerator}, devices={devices}")

z_query = query_model.get_latent_representation()
if z_query.shape[0] != adata_query_prepped.n_obs:
    fail(f"Unexpected query latent shape: {z_query.shape}")
ok(f"Query latent shape = {z_query.shape}")

print("\nAll scArches smoke tests passed.")