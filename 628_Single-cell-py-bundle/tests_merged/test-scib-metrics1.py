#!/usr/bin/env python3
import sys, traceback, platform, importlib.metadata as md
import numpy as np

def ver(name):
    try:
        return md.version(name)
    except Exception:
        return "not-installed"

def ok(msg):
    print(f"[OK] {msg}")

def info(msg):
    print(f"[INFO] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def fail(msg, code=1):
    print(f"[FAIL] {msg}")
    sys.exit(code)

try:
    import jax
    import jax.numpy as jnp
    import scib_metrics
    from scib_metrics.nearest_neighbors import jax_approx_min_k
except Exception as e:
    fail(f"Import error: {e}")

info(f"Python: {sys.version.split()[0]} ({platform.platform()})")
info(f"scib-metrics: {ver('scib-metrics')}")
info(f"jax: {ver('jax')}")
info(f"jaxlib: {ver('jaxlib')}")

if ver("scib-metrics") != "0.5.9":
    warn(f"Expected scib-metrics 0.5.9, found {ver('scib-metrics')}")

try:
    scib_metrics.settings.jax_preallocate_gpu_memory = False
    ok("Disabled JAX GPU memory preallocation")
except Exception as e:
    warn(f"Could not change scib_metrics.settings.jax_preallocate_gpu_memory: {e}")

try:
    devices = jax.devices()
    info("JAX devices: " + ", ".join(f"{d.platform}:{d.device_kind}" for d in devices))
except Exception as e:
    fail(f"Could not query JAX devices: {e}")

gpu_devices = [d for d in devices if d.platform == "gpu"]
if not gpu_devices:
    fail("JAX does not see any GPU device")

gpu = gpu_devices[0]
ok(f"Using GPU device: {gpu.device_kind}")

try:
    x = jax.device_put(jnp.arange(1024 * 1024, dtype=jnp.float32).reshape(1024, 1024), device=gpu)
    y = (x @ x.T).sum()
    y.block_until_ready()
    ok(f"JAX matmul executed on GPU, result={float(y):.3e}")
except Exception as e:
    print(traceback.format_exc())
    fail(f"JAX GPU compute failed: {e}")

try:
    rng = np.random.default_rng(0)
    n_labels = 4
    n_batches = 2
    per_group = 64
    d = 16

    xs, labels, batches = [], [], []
    centers = rng.normal(0, 3, size=(n_labels, d)).astype(np.float32)

    for lab in range(n_labels):
        for bat in range(n_batches):
            shift = np.zeros(d, dtype=np.float32)
            shift[bat] = 0.25
            block = centers[lab] + shift + rng.normal(0, 0.35, size=(per_group, d)).astype(np.float32)
            xs.append(block)
            labels.extend([f"label_{lab}"] * per_group)
            batches.extend([f"batch_{bat}"] * per_group)

    X = np.vstack(xs).astype(np.float32)
    labels = np.asarray(labels)
    batches = np.asarray(batches)

    info(f"Synthetic matrix shape: {X.shape}")
except Exception as e:
    fail(f"Could not build synthetic dataset: {e}")

try:
    nn = jax_approx_min_k(X, n_neighbors=15, chunk_size=128)
    ok(f"jax_approx_min_k ran successfully: indices={nn.indices.shape}, distances={nn.distances.shape}")
except Exception as e:
    print(traceback.format_exc())
    fail(f"scib-metrics neighbor search failed: {e}")

def to_scalar(x):
    arr = np.asarray(x)
    return float(arr.mean()) if arr.ndim > 0 else float(arr)

try:
    ilisi = scib_metrics.ilisi_knn(nn, batches, scale=True)
    ilisi_val = to_scalar(ilisi)
    if not np.isfinite(ilisi_val):
        fail("ilisi_knn returned a non-finite value")
    ok(f"ilisi_knn succeeded: mean={ilisi_val:.6f}")
except Exception as e:
    print(traceback.format_exc())
    fail(f"ilisi_knn failed: {e}")

try:
    gc = scib_metrics.graph_connectivity(nn, labels)
    gc_val = to_scalar(gc)
    if not np.isfinite(gc_val):
        fail("graph_connectivity returned a non-finite value")
    ok(f"graph_connectivity succeeded: value={gc_val:.6f}")
except Exception as e:
    print(traceback.format_exc())
    fail(f"graph_connectivity failed: {e}")

print("\n[PASS] scib-metrics + JAX CUDA smoke test completed successfully.")