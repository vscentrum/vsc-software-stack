
import sys, importlib, json, traceback
import jax, jax.numpy as jnp
import numpy as np
import jaxtyping as jt
from jaxtyping import Array, Float, Int, Bool
try:
    from jaxtyping import PRNGKeyArray
    HAVE_KEY=True
except Exception:
    HAVE_KEY=False
try:
    from beartype import beartype as _typechecker
except Exception:
    try:
        from typeguard import typechecked as _typechecker
    except Exception:
        _typechecker=None
def _jaxtyped(f): 
    return (jt.jaxtyped(typechecker=_typechecker)(f) if _typechecker else f)

def versions():
    return {"python":sys.version.split()[0],"jax":getattr(jax,"__version__",None),"jaxtyping":getattr(jt,"__version__",None)}

@_jaxtyped
def normalize(x: Float[Array,"b d"]) -> Float[Array,"b d"]:
    m=x.mean(1,keepdims=True); s=jnp.std(x,1,keepdims=True)+1e-6; return (x-m)/s

@_jaxtyped
def add_same(a: Float[Array,"b d"], b: Float[Array,"b d"]) -> Float[Array,"b d"]:
    return a+b

@_jaxtyped
def bmm(a: Float[Array,"b m k"], b: Float[Array,"b k n"]) -> Float[Array,"b m n"]:
    return a@b

@_jaxtyped
def cosine(u: Float[Array,"d"], v: Float[Array,"d"]) -> Float[Array,""]:
    return jnp.dot(u,v)/(jnp.linalg.norm(u)*jnp.linalg.norm(v)+1e-6)

if HAVE_KEY:
    @_jaxtyped
    def split_twice(key: PRNGKeyArray):
        k1,k2=jax.random.split(key); return k1,k2

def run():
    res={"versions":versions(),"runtime_typechecker":("beartype" if _typechecker and _typechecker.__name__.startswith("beartype") else ("typeguard" if _typechecker else None)),"checks":[],"errors":[],"skipped":[]}
    try:
        assert res["versions"]["jax"].startswith("0.6.2")
        res["checks"].append("jax_version_ok")
    except Exception as e:
        res["errors"].append(f"Expected JAX 0.6.2, found {res['versions']['jax']}")
    try:
        assert res["versions"]["jaxtyping"]=="0.2.38"
        res["checks"].append("jaxtyping_version_ok")
    except Exception:
        res["errors"].append(f"Expected jaxtyping 0.2.38, found {res['versions']['jaxtyping']}")
    try:
        x=jnp.arange(24.,dtype=jnp.float32).reshape(3,8); y=normalize(x); assert y.shape==(3,8) and jnp.issubdtype(y.dtype,jnp.floating)
        y_jit=jax.jit(normalize)(x); assert y_jit.shape==(3,8)
        res["checks"].append("normalize+jit_ok")
    except Exception as e:
        res["errors"].append("normalize_failed: "+repr(e))
    try:
        u=jnp.ones((32,64),jnp.float32); v=jnp.ones((32,64),jnp.float32); out=jax.vmap(cosine)(u,v); assert out.shape==(32,)
        res["checks"].append("vmap_ok")
    except Exception as e:
        res["errors"].append("vmap_failed: "+repr(e))
    try:
        a=jnp.ones((4,3,5),jnp.float32); b=jnp.ones((4,5,2),jnp.float32); out=bmm(a,b); assert out.shape==(4,3,2)
        res["checks"].append("bmm_ok")
    except Exception as e:
        res["errors"].append("bmm_failed: "+repr(e))
    if _typechecker:
        try:
            xi=jnp.arange(24,dtype=jnp.int32).reshape(3,8); normalize(xi); res["errors"].append("dtype_guard_expected_failure_but_passed")
        except Exception: res["checks"].append("dtype_mismatch_rejected")
        try:
            a=jnp.ones((3,8),jnp.float32); b=jnp.ones((3,7),jnp.float32); add_same(a,b); res["errors"].append("shape_guard_expected_failure_but_passed")
        except Exception: res["checks"].append("shape_mismatch_rejected")
    else:
        res["skipped"]+=["dtype_mismatch_rejected","shape_mismatch_rejected"]
    if HAVE_KEY:
        try:
            k=jax.random.key(0); k1,k2=split_twice(k); assert k1.shape==k.shape==k2.shape
            res["checks"].append("prngkey_ok")
        except Exception as e:
            res["errors"].append("prngkey_failed: "+repr(e))
    else:
        res["skipped"].append("prngkey_ok")
    try:
        b=jnp.array([True,False,True]); assert b.dtype==jnp.bool_
        res["checks"].append("bool_dtype_ok")
    except Exception as e:
        res["errors"].append("bool_dtype_failed: "+repr(e))
    ok= len(res["errors"])==0
    print(json.dumps(res,indent=2,sort_keys=True))
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(run())
