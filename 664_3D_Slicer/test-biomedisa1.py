#!/usr/bin/env python3

import importlib.metadata
import math
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np


def check(cond, msg):
    if not cond:
        raise RuntimeError(msg)


def section(name):
    print("\n" + "=" * 78)
    print(name)
    print("=" * 78)


def dist_version(name):
    return importlib.metadata.version(name)


def test_imports_and_versions():
    expected = {
        "biomedisa": "26.7.3",
        "keras": "3.15.1",
        "namex": "0.1.0",
        "MedPy": "0.5.2",
        "torch": "2.9.1",
        "torchvision": "0.24.1",
        "pycuda": "2025.1.2",
    }
    for name, wanted in expected.items():
        got = dist_version(name)
        print(f"{name:15s}: {got}")
        check(got == wanted or got.startswith(wanted + "+"),
              f"{name}: expected {wanted}, got {got}")

    import absl
    import cv2
    import h5py
    import keras
    import medpy
    import ml_dtypes
    import namex
    import numba
    import optree
    import scipy
    import SimpleITK
    import skimage
    import tifffile
    import torch
    import torchvision

    from biomedisa.deeplearning import deep_learning
    from biomedisa.features.biomedisa_helper import load_data, save_data
    from biomedisa.interpolation import smart_interpolation

    print(f"OpenCV          : {cv2.__version__}")
    print(f"h5py            : {h5py.__version__}")
    print(f"Numba           : {numba.__version__}")
    print(f"SciPy           : {scipy.__version__}")
    print(f"scikit-image    : {skimage.__version__}")
    print(f"SimpleITK       : {SimpleITK.Version_VersionString()}")
    print(f"ml_dtypes       : {ml_dtypes.__version__}")
    print(f"optree          : {optree.__version__}")

    check(callable(load_data), "Biomedisa load_data is not callable")
    check(callable(save_data), "Biomedisa save_data is not callable")
    check(callable(smart_interpolation), "Biomedisa smart_interpolation is not callable")
    check(callable(deep_learning), "Biomedisa deep_learning is not callable")


def test_helpers_and_io():
    import h5py
    from biomedisa.features.biomedisa_helper import Dice_score, img_resize, load_data, save_data

    data = np.arange(8 * 16 * 16, dtype=np.uint16).reshape(8, 16, 16)
    labels = np.zeros((8, 16, 16), dtype=np.uint8)
    labels[2:6, 4:12, 4:12] = 1

    dice = Dice_score(labels, labels)
    check(math.isclose(float(dice), 1.0), f"Dice_score(identity) returned {dice}")

    resized = img_resize(labels, (4, 8, 8), labels=True)
    check(resized.shape == (4, 8, 8), f"Unexpected resized shape: {resized.shape}")
    check(set(np.unique(resized)).issubset({0, 1}),
          f"Resize introduced labels {np.unique(resized)}")

    with tempfile.TemporaryDirectory(prefix="biomedisa-smoke-") as tmp:
        tmp = Path(tmp)

        tif = tmp / "volume.tif"
        save_data(str(tif), data, compress=False)
        loaded, _ = load_data(str(tif))
        check(np.array_equal(loaded, data), "Biomedisa TIFF round-trip failed")

        nrrd = tmp / "volume.nrrd"
        save_data(str(nrrd), data, compress=False)
        loaded, _ = load_data(str(nrrd))
        check(np.array_equal(loaded, data), "Biomedisa NRRD round-trip failed")

        h5 = tmp / "volume.h5"
        with h5py.File(h5, "w") as f:
            f.create_dataset("volume", data=data)
        with h5py.File(h5, "r") as f:
            check(np.array_equal(f["volume"][:], data), "h5py round-trip failed")


def test_numba():
    import numba

    @numba.njit
    def add_one(x):
        return x + 1

    x = np.arange(16, dtype=np.int64)
    check(np.array_equal(add_one(x), x + 1), "Numba JIT result is incorrect")


def test_keras_torch_backend():
    backend_env = os.environ.get("KERAS_BACKEND")
    print(f"KERAS_BACKEND env: {backend_env}")
    check(backend_env == "torch", f"Expected KERAS_BACKEND=torch, got {backend_env!r}")

    import keras

    backend = keras.backend.backend()
    print(f"Keras backend    : {backend}")
    check(backend == "torch", f"Keras backend is {backend!r}, expected 'torch'")

    x = np.arange(32, dtype=np.float32).reshape(8, 4) / 32.0
    y = np.zeros((8, 1), dtype=np.float32)

    model = keras.Sequential([
        keras.layers.Input(shape=(4,)),
        keras.layers.Dense(8, activation="relu"),
        keras.layers.Dense(1),
    ])
    model.compile(optimizer="sgd", loss="mse")
    pred = model(x, training=False)
    check(tuple(pred.shape) == (8, 1), f"Unexpected Keras output shape: {pred.shape}")
    loss = float(np.asarray(model.train_on_batch(x, y)))
    check(np.isfinite(loss), f"Keras returned invalid loss: {loss}")
    print(f"Keras train loss : {loss:.8g}")


def test_torch_torchvision_cuda():
    import torch
    import torchvision

    print(f"PyTorch          : {torch.__version__}")
    print(f"torchvision      : {torchvision.__version__}")
    print(f"PyTorch CUDA     : {torch.version.cuda}")
    print(f"CUDA available   : {torch.cuda.is_available()}")

    check(torch.cuda.is_available(), "PyTorch cannot access a CUDA device")
    check(torch.version.cuda is not None, "PyTorch has no CUDA support")
    check(str(torch.version.cuda).startswith("12.9"),
          f"Expected CUDA 12.9 PyTorch build, got {torch.version.cuda}")
    print(f"CUDA device 0    : {torch.cuda.get_device_name(0)}")

    a = torch.arange(256, dtype=torch.float32, device="cuda").reshape(16, 16)
    result = a @ a.T
    check(result.is_cuda and torch.isfinite(result).all().item(), "PyTorch CUDA calculation failed")

    check(torchvision.extension._has_ops(), "torchvision compiled ops are unavailable")
    boxes = torch.tensor([
        [0.0, 0.0, 10.0, 10.0],
        [1.0, 1.0, 9.0, 9.0],
        [20.0, 20.0, 30.0, 30.0],
    ], device="cuda")
    scores = torch.tensor([0.9, 0.8, 0.7], device="cuda")
    keep = torchvision.ops.nms(boxes, scores, 0.5)
    check(keep.is_cuda, "torchvision NMS did not run on CUDA")
    check(keep.cpu().tolist() == [0, 2], f"Unexpected NMS result: {keep.cpu().tolist()}")


def test_opencv_cuda():
    import cv2

    count = cv2.cuda.getCudaEnabledDeviceCount()
    print(f"OpenCV CUDA GPUs : {count}")
    check(count > 0, "OpenCV cannot access a CUDA device")

    src = np.arange(64, dtype=np.uint8).reshape(8, 8)
    gpu = cv2.cuda_GpuMat()
    gpu.upload(src)
    check(np.array_equal(gpu.download(), src), "OpenCV CUDA GpuMat transfer failed")


def test_biomedisa_pycuda():
    cmd = [sys.executable, "-s", "-m", "biomedisa.features.pycuda_test"]
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    check(proc.returncode == 0, f"Biomedisa PyCUDA test exited with {proc.returncode}")
    check("PyCUDA test okay!" in proc.stdout, "Biomedisa PyCUDA test did not report success")


def test_smart_interpolation_cuda():
    from biomedisa.interpolation import smart_interpolation

    zsh, ysh, xsh = 20, 24, 24
    z, y, x = np.indices((zsh, ysh, xsh))
    radius2 = (y - ysh / 2.0) ** 2 + (x - xsh / 2.0) ** 2

    data = np.where(radius2 <= 36.0, 220, 30).astype(np.uint8)
    data = data + ((z % 3) * 2).astype(np.uint8)

    labels = np.zeros((zsh, ysh, xsh), dtype=np.uint8)
    object_mask = radius2 <= 25.0
    labels[5][object_mask[5]] = 1
    labels[14][object_mask[14]] = 1

    results = smart_interpolation(
        data,
        labels,
        nbrw=1,
        sorw=20,
        platform="cuda_force",
        smooth=0,
        uncertainty=False,
    )

    check(isinstance(results, dict), f"smart_interpolation returned {type(results)}")
    check("regular" in results, f"Result keys are {list(results)}")

    result = results["regular"]
    print(f"Interpolation shape : {result.shape}")
    print(f"Interpolation labels: {np.unique(result)}")
    check(result.shape == data.shape, f"Unexpected interpolation shape: {result.shape}")
    check(set(np.unique(result)).issubset({0, 1}),
          f"Unexpected interpolation labels: {np.unique(result)}")
    check(np.any(result == 1), "Smart interpolation produced no foreground")


def main():
    tests = [
        ("Imports and versions", test_imports_and_versions),
        ("Biomedisa helper functions and I/O", test_helpers_and_io),
        ("Numba JIT", test_numba),
        ("Keras with Torch backend", test_keras_torch_backend),
        ("PyTorch and torchvision CUDA", test_torch_torchvision_cuda),
        ("OpenCV CUDA", test_opencv_cuda),
        ("Biomedisa upstream PyCUDA test", test_biomedisa_pycuda),
        ("Biomedisa smart interpolation on CUDA", test_smart_interpolation_cuda),
    ]

    print("Biomedisa installation smoke test")
    print(f"Python           : {sys.version.split()[0]}")
    print(f"Executable       : {sys.executable}")

    try:
        for name, func in tests:
            section(name)
            func()
            print(f"[ OK ] {name}")
    except Exception:
        print("\nSMOKE TEST FAILED")
        traceback.print_exc()
        return 1

    print("\n" + "=" * 78)
    print("ALL BIOMEDISA SMOKE TESTS PASSED")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
