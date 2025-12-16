import onnxruntime as ort

def main():
    print("onnxruntime version:", ort.__version__)
    print("default device:", ort.get_device())
    providers = ort.get_available_providers()
    print("available providers:", providers)
    if "CUDAExecutionProvider" in providers:
        print("CUDAExecutionProvider is available")
    else:
        print("CUDAExecutionProvider is NOT available")
    if hasattr(ort, "get_build_info"):
        info = ort.get_build_info()
        print("build info:")
        for k in sorted(info):
            print(" ", k, "=", info[k])

if __name__ == "__main__":
    main()
