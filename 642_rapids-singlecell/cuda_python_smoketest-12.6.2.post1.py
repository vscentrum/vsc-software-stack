import ctypes
import importlib.metadata as md

print("== package versions ==")
for pkg in ["cuda-python", "cuda-core", "pyclibrary"]:
    try:
        print(f"{pkg}: {md.version(pkg)}")
    except md.PackageNotFoundError:
        print(f"{pkg}: NOT INSTALLED")

print("\n== python imports ==")
import cuda
from cuda import cuda as cu, nvrtc
from cuda.bindings import driver, nvrtc as nvrtc_bind
from cuda.core.experimental import Program, ProgramOptions

print("cuda module:", getattr(cuda, "__file__", "<no __file__>"))
print("driver module:", getattr(driver, "__file__", "<no __file__>"))
print("nvrtc module:", getattr(nvrtc, "__file__", "<no __file__>"))
print("cuda.core Program:", Program)
print("cuda.core ProgramOptions:", ProgramOptions)

print("\n== shared libraries ==")
ctypes.CDLL("libcuda.so.1")
ctypes.CDLL("libnvrtc.so")
print("libcuda.so.1: OK")
print("libnvrtc.so:   OK")

def check_cu(res, what):
    if res != cu.CUresult.CUDA_SUCCESS:
        raise RuntimeError(f"{what} failed: {res}")

def check_nvrtc(res, what, prog=None):
    if res != nvrtc.nvrtcResult.NVRTC_SUCCESS:
        msg = str(res)
        if prog is not None:
            try:
                err, logsize = nvrtc.nvrtcGetProgramLogSize(prog)
                if err == nvrtc.nvrtcResult.NVRTC_SUCCESS and logsize > 1:
                    log = bytearray(logsize)
                    (err,) = nvrtc.nvrtcGetProgramLog(prog, log)
                    if err == nvrtc.nvrtcResult.NVRTC_SUCCESS:
                        msg = bytes(log).decode(errors="replace")
            except Exception:
                pass
        raise RuntimeError(f"{what} failed:\n{msg}")

print("\n== CUDA driver ==")
(err,) = cu.cuInit(0)
check_cu(err, "cuInit")

err, drv_ver = cu.cuDriverGetVersion()
check_cu(err, "cuDriverGetVersion")
print("driver version:", drv_ver)

err, ndev = cu.cuDeviceGetCount()
check_cu(err, "cuDeviceGetCount")
print("device count:", ndev)
if ndev < 1:
    raise RuntimeError("No CUDA devices found")

err, dev = cu.cuDeviceGet(0)
check_cu(err, "cuDeviceGet(0)")

err, name = cu.cuDeviceGetName(100, dev)
check_cu(err, "cuDeviceGetName")
if isinstance(name, bytes):
    name = name.decode(errors="replace")
print("device 0:", name)

err, major, minor = cu.cuDeviceComputeCapability(dev)
check_cu(err, "cuDeviceComputeCapability")
print("compute capability:", f"{major}.{minor}")

print("\n== NVRTC compile ==")
src = r'''
extern "C" __global__
void add1(const float* x, float* y, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) y[i] = x[i] + 1.0f;
}
'''
arch = f"--gpu-architecture=compute_{major}{minor}".encode()

err, prog = nvrtc.nvrtcCreateProgram(src.encode(), b"add1.cu", 0, [], [])
check_nvrtc(err, "nvrtcCreateProgram")

opts = [arch]
(err,) = nvrtc.nvrtcCompileProgram(prog, len(opts), opts)
check_nvrtc(err, "nvrtcCompileProgram", prog=prog)

err, ptx_size = nvrtc.nvrtcGetPTXSize(prog)
check_nvrtc(err, "nvrtcGetPTXSize", prog=prog)

ptx = bytearray(ptx_size)
(err,) = nvrtc.nvrtcGetPTX(prog, ptx)
check_nvrtc(err, "nvrtcGetPTX", prog=prog)

(err,) = nvrtc.nvrtcDestroyProgram(prog)
check_nvrtc(err, "nvrtcDestroyProgram")

print("PTX size:", ptx_size)
print("PTX header:", bytes(ptx[:80]).decode(errors="replace").splitlines()[0])

print("\nALL OK")