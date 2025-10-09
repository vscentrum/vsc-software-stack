
import os, sys, time, shutil, importlib
try:
    from importlib.metadata import version as _ver
except Exception:
    _ver = lambda name: "unknown"

def _v(name):
    try: return _ver(name)
    except Exception: return "unknown"

def _kv(k,v): print(f"{k}: {v}")

def main():
    ok=True
    _kv("python", sys.version.split()[0])
    # package versions
    pkgs=[("alphafold3","alphafold3"),("jax","jax"),("jaxlib","jaxlib"),("jax-triton","jax-triton"),("triton","triton"),("rdkit","rdkit")]
    for k,p in pkgs: _kv(k,_v(p))
    # env hints
    for k in ["XLA_FLAGS","XLA_PYTHON_CLIENT_PREALLOCATE","TF_FORCE_UNIFIED_MEMORY","XLA_CLIENT_MEM_FRACTION","AF3_MODEL_DIR","TRITON_HOME"]:
        _kv(k, os.environ.get(k,""))
    # CLI presence
    _kv("run_alphafold.py", shutil.which("run_alphafold.py") or "")
    # JAX device + jit sanity
    import jax, jax.numpy as jnp, numpy as np
    _kv("jax_backend", jax.default_backend())
    devs=jax.devices()
    _kv("devices", ", ".join([f"{d.platform}:{getattr(d,'device_kind',str(d))}" for d in devs]))
    @jax.jit
    def mm(a,b): return a@b
    a=jnp.ones((1024,1024), dtype=jnp.float16); b=jnp.ones((1024,1024), dtype=jnp.float16)
    t=time.time(); c=mm(a,b).block_until_ready(); dt=time.time()-t
    _kv("jit_matmul_ms", int(dt*1000)); _kv("jit_matmul_sum", float(c.sum()))
    # jax-triton import
    try:
        import jax_triton as jt
        _kv("jax_triton_import","ok")
    except Exception as e:
        ok=False; _kv("jax_triton_error", repr(e))
    # triton import
    try:
        import triton
        _kv("triton_import","ok")
    except Exception as e:
        ok=False; _kv("triton_error", repr(e))
    # HMMER presence
    hmmbins=["jackhmmer","nhmmer","hmmalign","hmmsearch","hmmbuild"]
    missing=[b for b in hmmbins if not shutil.which(b)]
    _kv("hmmer_missing", ",".join(missing))
    if missing: ok=False
    # RDKit sanity
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mw=Descriptors.MolWt(Chem.MolFromSmiles("CCO"))
        _kv("rdkit_molwt_CCO", round(mw,3))
    except Exception as e:
        ok=False; _kv("rdkit_error", repr(e))
    _kv("result", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__=="__main__": main()
