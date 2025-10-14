# attn_compare_masked.py
import os
import jax
import jax.numpy as jnp

from alphafold3.jax.attention import flash_attention as fa
from alphafold3.jax.common import array_view
from alphafold3.jax.common import precision as precision_lib

# keep GPU memory use modest
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

# --- config ---
B, T, H, D = 1, 128, 2, 64   # query shape:  (B, T, H, D)
t, h = T, H                  # key/value shape: (B, t, h, D); usually t=T and h=H
is_causal = False            # toggle to True to also test causal masking
mask_keep_prob = 0.85        # probability a position is kept (True) in the mask
seed = 0

# --- inputs ---
key = jax.random.key(seed)
k_q, k_k, k_v, k_m = jax.random.split(key, 4)

q = jax.random.normal(k_q, (B, T, H, D), dtype=jnp.float16)
k = jax.random.normal(k_k, (B, t, h, D), dtype=jnp.float16)
v = jax.random.normal(k_v, (B, t, h, D), dtype=jnp.float16)

# Boolean mask as AF3 expects: (B, H, T, t)
# mask = jax.random.bernoulli(k_m, p=mask_keep_prob, shape=(B, H, T, t))
mask = jnp.ones((B, H, T, t), dtype=bool)


# scale like AF3
scale = float(1.0 / jnp.sqrt(D))

# --- Triton path (your patched kernel) ---
o_triton = fa._fwd(
    array_view.ArrayView(q),
    array_view.ArrayView(k),
    array_view.ArrayView(v),
    bias=None,
    # mask=array_view.ArrayView(mask.astype(jnp.bool_)),  # (B, H, T, t)
    mask=None,
    k_start=None,
    k_end=None,
    logits_scale=scale,
    is_causal=is_causal,
    q_k_dot_precision=precision_lib.DotPrecision.F32_F32,
    weights_v_dot_precision=precision_lib.DotPrecision.F32_F32,
)

# --- Pure-JAX reference path ---
q_f32 = q.astype(jnp.float32)
k_f32 = k.astype(jnp.float32)
v_f32 = v.astype(jnp.float32)

# logits: (B, T, H, t). Heads align by using the same 'H' label in both args.
scores = jnp.einsum("bTHd,btHd->bTHt", q_f32, k_f32) * scale

# apply the same mask: transpose (B,H,T,t) -> (B,T,H,t) to match scores
mask_ref = jnp.transpose(mask, (0, 2, 1, 3))  # (B, T, H, t)

# use same sentinel as kernel (very negative float32)
mask_value = jnp.finfo(jnp.float32).min
scores = jnp.where(mask_ref, scores, jnp.array(mask_value, dtype=scores.dtype))

# optional causal masking on reference as well
if is_causal:
    causal = jnp.tril(jnp.ones((T, t), dtype=bool))
    scores = jnp.where(causal[None, :, None, :], scores, jnp.array(mask_value, dtype=scores.dtype))

probs = jax.nn.softmax(scores, axis=-1)
o_ref = jnp.einsum("bTHt,btHd->bTHd", probs, v_f32).astype(q.dtype)

# --- compare ---
diff = jnp.abs(o_triton - o_ref)
max_abs = jnp.max(diff)
max_rel = jnp.max(jnp.abs(diff / (jnp.abs(o_ref) + 1e-6)))

print("o_triton slice:\n", jnp.asarray(o_triton[0, :8, 0, :6]))
print("o_ref    slice:\n", jnp.asarray(o_ref[0, :8, 0, :6]))
print("diff     slice:\n", jnp.asarray(diff[0, :8, 0, :6]))
print("o_triton min/max:", float(jnp.min(o_triton)), float(jnp.max(o_triton)))
print("o_ref    min/max:", float(jnp.min(o_ref)),    float(jnp.max(o_ref)))
print("max_abs:", float(max_abs))
print("max_rel:", float(max_rel))
