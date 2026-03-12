import os, sys, platform
import cupy as cp

def main():
    print("python:", sys.version.split()[0])
    print("platform:", platform.platform())
    print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>"))
    n = cp.cuda.runtime.getDeviceCount()
    assert n >= 1, "No CUDA device visible to CuPy"
    dev = cp.cuda.Device(0)
    props = cp.cuda.runtime.getDeviceProperties(0)
    print("gpu_count:", n)
    print("gpu0_name:", props["name"].decode())
    print("gpu0_cc:", f'{props["major"]}.{props["minor"]}')
    x = cp.arange(1_000_000, dtype=cp.float32)
    s = float(x.sum(dtype=cp.float64).get())
    assert s == 499999500000.0, f"Unexpected CuPy sum: {s}"
    y = cp.random.random((2048, 256), dtype=cp.float32)
    z = cp.linalg.norm(y, axis=1)
    assert z.shape == (2048,)
    assert bool(cp.isfinite(z).all().get())
    free_b, total_b = cp.cuda.runtime.memGetInfo()
    print("gpu_mem_free_gb:", round(free_b / 1024**3, 2))
    print("gpu_mem_total_gb:", round(total_b / 1024**3, 2))
    print("OK: CUDA via CuPy works")

if __name__ == "__main__":
    main()