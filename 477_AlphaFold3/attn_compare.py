import os
import jax
import jax.numpy as jnp
from alphafold3.jax.attention import flash_attention as fa
from alphafold3.jax.common import array_view
from alphafold3.jax.common import precision as precision_lib

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

key = jax.random.key(0)
B, T, H, D = 1, 32, 1, 32   # smaller, single head, single kv block
t, h = T, H

q = jax.random.normal(key, (B, T, H, D), dtype=jnp.float16)
k = jax.random.normal(jax.random.split(key)[0], (B, t, h, D), dtype=jnp.float16)
v = jnp.ones((B, t, h, D), dtype=jnp.float16)

scale = float(1.0 / jnp.sqrt(D))

# Triton
# --- keep the rest of your script the same up to scale ---

# Triton path (patched kernel) — set causal=True
o_triton = fa._fwd(
    array_view.ArrayView(q),
    array_view.ArrayView(k),
    array_view.ArrayView(v),
    bias=None,
    mask=None,
    k_start=None,
    k_end=None,
    logits_scale=scale,
    is_causal=True,  # <— changed
    q_k_dot_precision=precision_lib.DotPrecision.F32_F32,
    weights_v_dot_precision=precision_lib.DotPrecision.F32_F32,
)

# Reference with causal mask
q_f32, k_f32, v_f32 = q.astype(jnp.float32), k.astype(jnp.float32), v.astype(jnp.float32)
scores = jnp.einsum("bTHd,bthd->bTHt", q_f32, k_f32) * scale

T_ref, t_ref = scores.shape[1], scores.shape[3]
causal = (jnp.arange(T_ref)[:, None] >= jnp.arange(t_ref)[None, :])[None, None, :, :]  # [1,1,T,t]
scores = jnp.where(causal, scores, -1e9)

probs = jax.nn.softmax(scores, axis=-1)
o_ref = jnp.einsum("bTHt,bthd->bTHd", probs, v_f32).astype(q.dtype)

# Compare
max_abs = jnp.max(jnp.abs(o_triton - o_ref))
max_rel = jnp.max(jnp.abs((o_triton - o_ref) / (jnp.abs(o_ref) + 1e-6)))
print("max_abs:", float(max_abs))
print("max_rel:", float(max_rel))
