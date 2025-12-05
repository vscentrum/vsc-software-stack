import pathlib, sys, numpy as np, onnx
from onnx import helper, TensorProto, checker, shape_inference, defs

def build_and_check(path):
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 3])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None, 2])
    W = np.random.randn(3, 2).astype("float32")
    b = np.random.randn(2).astype("float32")
    W_init = helper.make_tensor("W", TensorProto.FLOAT, W.shape, W.ravel())
    b_init = helper.make_tensor("b", TensorProto.FLOAT, b.shape, b)
    node = helper.make_node("Gemm", ["X", "W", "b"], ["Y"])
    graph = helper.make_graph([node], "LinearModel", [X], [Y], [W_init, b_init])
    opset = helper.make_operatorsetid("", defs.onnx_opset_version())
    model = helper.make_model(graph, opset_imports=[opset])
    checker.check_model(model)
    inferred = shape_inference.infer_shapes(model)
    checker.check_model(inferred)
    onnx.save(inferred, path)
    loaded = onnx.load(path)
    checker.check_model(loaded)
    print("Saved model to:", path)
    print("Model IR version:", loaded.ir_version)
    print("PASS: model build/check/shape-inference/round-trip")

def main():
    out = pathlib.Path("linear.onnx")
    try:
        build_and_check(str(out))
    except Exception as e:
        print("FAIL:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
