import sys, onnx
from onnx import defs

def main():
    print("Python:", sys.version.replace("\n", " "))
    print("Executable:", sys.executable)
    print("ONNX version:", onnx.__version__)
    print("ONNX package file:", onnx.__file__)
    print("Default ONNX opset:", defs.onnx_opset_version())
    print("PASS: basic ONNX import and metadata")

if __name__ == "__main__":
    main()
