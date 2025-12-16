import tempfile, pathlib
import numpy as np
import onnx
from onnx import helper, TensorProto
import onnxruntime as ort


def build_toy_model(path, ir_version=11, opset_version=11):
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 3])
    W = helper.make_tensor_value_info("W", TensorProto.FLOAT, [3, 2])
    B = helper.make_tensor_value_info("B", TensorProto.FLOAT, [2])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 2])

    mm = helper.make_node("MatMul", ["X", "W"], ["Z"])
    add = helper.make_node("Add", ["Z", "B"], ["Y"])

    graph = helper.make_graph(
        [mm, add],
        "toy-matmul-add",
        [X, W, B],
        [Y],
    )

    model = helper.make_model(
        graph,
        producer_name="toy-test",
        ir_version=ir_version,
        opset_imports=[helper.make_opsetid("", opset_version)],
    )
    onnx.save(model, path)


def run_with_providers(model_path, providers):
    print("available providers:", ort.get_available_providers())
    print("running with providers:", providers)

    so = ort.SessionOptions()
    # Optional: avoid the pthread_setaffinity_np spam on the cluster
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1

    sess = ort.InferenceSession(model_path, sess_options=so, providers=providers)

    x = np.random.rand(1, 3).astype(np.float32)
    w = np.random.rand(3, 2).astype(np.float32)
    b = np.random.rand(2).astype(np.float32)

    outputs = sess.run(None, {"X": x, "W": w, "B": b})
    y = outputs[0]
    print("Y shape:", y.shape, "dtype:", y.dtype)


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        toy_path = pathlib.Path(tmpdir) / "toy.onnx"
        build_toy_model(toy_path.as_posix())
        print("created model at:", toy_path)

        # CUDA + CPU fallback
        run_with_providers(
            toy_path.as_posix(),
            ["CUDAExecutionProvider", "CPUExecutionProvider"],
        )


if __name__ == "__main__":
    main()
