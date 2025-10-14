import os
import jax
import jax.numpy as jnp

from alphafold3.jax.attention import flash_attention as fa
from alphafold3.jax.common import array_view
from alphafold3.jax.common import precision as precision_lib

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

key = jax.random.key(0)
B, T, H, D = 1, 128, 2, 64
t, h = T, H

q = jax.random.normal(key,                    (B, T, H, D), dtype=jnp.float16)
k = jax.random.normal(jax.random.split(key)[0], (B, t, h, D), dtype=jnp.float16)
v = jax.random.normal(jax.random.split(key)[1], (B, t, h, D), dtype=jnp.float16)

scale = float(1.0 / jnp.sqrt(D))

# --- Build a mask in the *scores* layout (B, T, H, T) for the reference ---
mask_scores = jax.random.bernoulli(jax.random.PRNGKey(1), p=0.8, shape=(B, T, H, T))
mask_scores = mask_scores.astype(jnp.bool_)

# Convert mask to the *kernel* layout (B, H, T, T) before passing to _fwd
mask_kernel = jnp.transpose(mask_scores, (0, 2, 1, 3))  # (B,H,T,T)

# Triton path (patched kernel) with mask
o_triton = fa._fwd(
    array_view.ArrayView(q),
    array_view.ArrayView(k),
    array_view.ArrayView(v),
    bias=None,
    mask=array_view.ArrayView(mask_kernel),
    k_start=None,
    k_end=None,
    logits_scale=scale,
    is_causal=False,
    q_k_dot_precision=precision_lib.DotPrecision.F32_F32,
    weights_v_dot_precision=precision_lib.DotPrecision.F32_F32,
)

# Reference attention (same mask but in scores layout)
q_f32, k_f32, v_f32 = q.astype(jnp.float32), k.astype(jnp.float32), v.astype(jnp.float32)
scores = jnp.einsum("bTHd,btHd->bTHt", q_f32, k_f32) * scale
scores = jnp.where(mask_scores, scores, jnp.array(-1e9, dtype=scores.dtype))
probs  = jax.nn.softmax(scores, axis=-1)
o_ref  = jnp.einsum("bTHt,btHd->bTHd", probs, v_f32).astype(q.dtype)

# Compare
diff = o_triton - o_ref
print("o_triton slice:\n", jnp.array(o_triton[0, :8, 0, :6]))
print("o_ref    slice:\n", jnp.array(o_ref[0, :8, 0, :6]))
print("diff     slice:\n", jnp.array(diff[0, :8, 0, :6]))
print("o_triton min/max:", float(o_triton.min()), float(o_triton.max()))
print("o_ref    min/max:", float(o_ref.min()), float(o_ref.max()))
max_abs = jnp.max(jnp.abs(diff))
max_rel = jnp.max(jnp.abs(diff) / (jnp.abs(o_ref) + 1e-6))
print("max_abs:", float(max_abs))
print("max_rel:", float(max_rel))
