# -*- coding: utf-8 -*-
import numpy as np
import ml_dtypes as mld
import jax, jax.numpy as jnp

print("ml_dtypes:", mld.__version__)
print("jax:", jax.__version__)

x_bf = np.asarray([1,2,3], dtype=mld.bfloat16)
y_bf = jnp.asarray(x_bf)
print("bfloat16 roundtrip dtype:", y_bf.dtype)

float8_names = [n for n in dir(mld) if n.startswith("float8")]
if float8_names:
    t = getattr(mld, float8_names[0])
    x_f8 = np.asarray([0,1,2], dtype=t)
    y_f8 = jnp.asarray(x_f8).astype(jnp.float32)
    print("float8 present:", float8_names[0], "-> cast to", y_f8.dtype)
else:
    print("float8 not present; skipping float8 check.")

@jax.jit
def sum_(z): return jnp.sum(z)
print("jit sum on bfloat16:", sum_(y_bf).item())
