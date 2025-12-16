import sys, pathlib
import numpy as np
import onnxruntime as ort

def make_input_array(ort_type, shape):
    dtype_map = {
        "tensor(float16)": np.float16,
        "tensor(float)": np.float32,
        "tensor(double)": np.float64,
        "tensor(int64)": np.int64,
        "tensor(int32)": np.int32,
        "tensor(int16)": np.int16,
        "tensor(int8)": np.int8,
        "tensor(uint8)": np.uint8,
    }
    dt = dtype_map.get(ort_type, np.float32)
    dims = []
    for d in shape:
        if isinstance(d, int) and d > 0:
            dims.append(d)
        else:
            dims.append(1)
    if not dims:
        dims = [1]
    if np.issubdtype(dt, np.floating):
        return np.random.randn(*dims).astype(dt)
    return np.random.randint(0, 10, size=dims, dtype=dt)

def main():
    if len(sys.argv) < 2:
        print("usage: python test_inference_with_model.py model.onnx [cpu|cuda]")
        sys.exit(1)
    model = pathlib.Path(sys.argv[1])
    if not model.is_file():
        print("model not found:", model)
        sys.exit(1)
    target = "cpu"
    if len(sys.argv) > 2:
        target = sys.argv[2].lower()
    available = ort.get_available_providers()
    preferred = []
    if target == "cuda" and "CUDAExecutionProvider" in available:
        preferred.append("CUDAExecutionProvider")
    if "CPUExecutionProvider" in available:
        preferred.append("CPUExecutionProvider")
    if not preferred:
        print("no suitable providers; available:", available)
        sys.exit(1)
    sess = ort.InferenceSession(model.as_posix(), providers=preferred)
    print("session providers:", sess.get_providers())
    feeds = {}
    for inp in sess.get_inputs():
        if not inp.type.startswith("tensor("):
            print("skipping non-tensor input:", inp.name, inp.type)
            continue
        arr = make_input_array(inp.type, inp.shape)
        feeds[inp.name] = arr
        print("input", inp.name, "shape", arr.shape, "dtype", arr.dtype)
    if not feeds:
        print("no usable tensor inputs; nothing to run")
        sys.exit(1)
    outputs = sess.run(None, feeds)
    print("inference OK; got", len(outputs), "outputs")
    for i, out in enumerate(outputs):
        try:
            s = out.shape
            d = out.dtype
        except Exception:
            s = "n/a"
            d = type(out)
        print(" output", i, "shape", s, "dtype", d)

if __name__ == "__main__":
    main()
