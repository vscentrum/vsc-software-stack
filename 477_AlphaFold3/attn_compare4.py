# attn_compare_bias.py
import os
import jax
import jax.numpy as jnp

from alphafold3.jax.attention import flash_attention as fa
from alphafold3.jax.common import array_view
from alphafold3.jax.common import precision as precision_lib

# Keep GPU memory use modest
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

key = jax.random.key(0)

# Shapes
B, T, H, D = 1, 128, 2, 64
t = T  # keys length

# Random test tensors
q = jax.random.normal(key,                 (B, T, H, D), dtype=jnp.float16)
k = jax.random.normal(jax.random.split(key)[0], (B, t, H, D), dtype=jnp.float16)
v = jax.random.normal(jax.random.split(key)[1], (B, t, H, D), dtype=jnp.float16)

# Build a causal-like mask (allowed if key_pos <= query_pos)
# Shape (T, t) -> broadcast to (B, H, T, t)
causal_Tt = (jnp.arange(T)[:, None] >= jnp.arange(t)[None, :])
mask_bool = jnp.broadcast_to(causal_Tt, (B, H, T, t))

# Encode mask as bias: keep allowed logits, strongly suppress disallowed
bias = jnp.where(mask_bool, 0.0, jnp.array(-1e9, dtype=jnp.float32)).astype(jnp.float32)

# Scale for attention logits
scale = float(1.0 / jnp.sqrt(D))

# ---- Triton path (mask disabled; bias used) ----
o_triton = fa._fwd(
    array_view.ArrayView(q),
    array_view.ArrayView(k),
    array_view.ArrayView(v),
    bias=array_view.ArrayView(bias),   # use bias-encoded mask
    mask=None,                         # disable mask path
    k_start=None,
    k_end=None,
    logits_scale=scale,
    is_causal=False,
    q_k_dot_precision=precision_lib.DotPrecision.F32_F32,
    weights_v_dot_precision=precision_lib.DotPrecision.F32_F32,
)

# ---- Pure JAX reference (apply same bias to logits) ----
q_f32 = q.astype(jnp.float32)
k_f32 = k.astype(jnp.float32)
v_f32 = v.astype(jnp.float32)

# scores shape: (B, T, H, t)
scores = jnp.einsum("bTHd,btHd->bTHt", q_f32, k_f32) * scale

# bias is (B, H, T, t) — transpose to (B, T, H, t) to match scores
bias_scores = jnp.transpose(bias, (0, 2, 1, 3))
scores = scores + bias_scores

probs = jax.nn.softmax(scores, axis=-1)
o_ref = jnp.einsum("bTHt,btHd->bTHd", probs, v_f32).astype(q.dtype)

# ---- Compare & print diagnostics ----
def to_host(x):  # ensure printing works under JIT/pjit
    return jnp.array(x).block_until_ready()

o_triton_h = to_host(o_triton)
o_ref_h    = to_host(o_ref)

sl = (slice(0,1), slice(0,8), slice(0,1))  # B=0, first 8 tokens, H=0
print("o_triton slice:\n", jnp.squeeze(o_triton_h[sl])[:, :6])
print("o_ref    slice:\n", jnp.squeeze(o_ref_h[sl])[:, :6])
print("diff     slice:\n", jnp.squeeze((o_triton_h - o_ref_h)[sl])[:, :6])

print("o_triton min/max:", float(o_triton_h.min()), float(o_triton_h.max()))
print("o_ref    min/max:", float(o_ref_h.min()),    float(o_ref_h.max()))

max_abs = jnp.max(jnp.abs(o_triton_h - o_ref_h))
max_rel = jnp.max(jnp.abs((o_triton_h - o_ref_h) / (jnp.abs(o_ref_h) + 1e-6)))
print("max_abs:", float(max_abs))
print("max_rel:", float(max_rel))
