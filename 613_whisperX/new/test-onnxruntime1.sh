#!/usr/bin/env bash
set -euo pipefail

export PYTHONNOUSERSITE=1
expected_version="${ONNXRUNTIME_EXPECTED_VERSION:-1.26.0}"

python -s - "${expected_version}" <<'PY'
import sys
from importlib.metadata import version
import numpy as np
import onnx
from onnx import TensorProto, helper
import onnxruntime as ort

expected = sys.argv[1]
actual = version("onnxruntime")
print(f"onnxruntime: {actual}")
assert actual == expected, (actual, expected)

providers = ort.get_available_providers()
print(f"Available providers: {providers}")
assert "CUDAExecutionProvider" in providers, providers

x_info = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2, 2])
w_info = helper.make_tensor_value_info("W", TensorProto.FLOAT, [2, 2])
b_info = helper.make_tensor_value_info("B", TensorProto.FLOAT, [2, 2])
y_info = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2, 2])

nodes = [
    helper.make_node("MatMul", ["X", "W"], ["M"]),
    helper.make_node("Add", ["M", "B"], ["Y"]),
]

graph = helper.make_graph(nodes, "ort_cuda_smoke", [x_info, w_info, b_info], [y_info])
model = helper.make_model(
    graph,
    producer_name="onnxruntime-easybuild-smoketest",
    opset_imports=[helper.make_opsetid("", 18)],
)
model.ir_version = 9
onnx.checker.check_model(model)

session = ort.InferenceSession(
    model.SerializeToString(),
    providers=[("CUDAExecutionProvider", {"device_id": 0})],
)

active = session.get_providers()
print(f"Session providers: {active}")
assert active[0] == "CUDAExecutionProvider", active

x = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
w = np.array([[2.0, 0.0], [0.0, 3.0]], dtype=np.float32)
b = np.array([[1.0, 1.0], [1.0, 1.0]], dtype=np.float32)
expected_y = x @ w + b

x_gpu = ort.OrtValue.ortvalue_from_numpy(x, "cuda", 0)
w_gpu = ort.OrtValue.ortvalue_from_numpy(w, "cuda", 0)
b_gpu = ort.OrtValue.ortvalue_from_numpy(b, "cuda", 0)

io = session.io_binding()
io.bind_ortvalue_input("X", x_gpu)
io.bind_ortvalue_input("W", w_gpu)
io.bind_ortvalue_input("B", b_gpu)
io.bind_output("Y", "cuda", 0)

session.run_with_iobinding(io)

gpu_outputs = io.get_outputs()
assert len(gpu_outputs) == 1
print(f"Output device: {gpu_outputs[0].device_name()}")
assert gpu_outputs[0].device_name() == "cuda"

y = io.copy_outputs_to_cpu()[0]
print("Result:")
print(y)
print("Expected:")
print(expected_y)

np.testing.assert_allclose(y, expected_y, rtol=1e-6, atol=1e-6)

print("== ONNX Runtime CUDA smoke test passed ==")
PY