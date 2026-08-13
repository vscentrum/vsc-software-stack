#!/usr/bin/env bash
set -euo pipefail

export PYTHONNOUSERSITE=1

python -s - <<'PY'
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import torch
import torchvision
from PIL import Image
from torchvision.io import decode_image
from torchvision.ops import nms
from torchvision.transforms import v2


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

torch_version = version("torch")
torchvision_version = version("torchvision")

print(f"PyTorch:      {torch_version}")
print(f"torchvision:  {torchvision_version}")
print(f"PyTorch CUDA: {torch.version.cuda}")

assert torch_version.split("+")[0] == "2.9.1", torch_version
assert torchvision_version == "0.24.1", torchvision_version
assert torch.version.cuda == "12.8", torch.version.cuda
assert torch.cuda.is_available()

print(f"GPU: {torch.cuda.get_device_name(0)}")


# ---------------------------------------------------------------------------
# Native torchvision CUDA operator
# ---------------------------------------------------------------------------

boxes = torch.tensor(
    [
        [0.0, 0.0, 10.0, 10.0],
        [1.0, 1.0, 11.0, 11.0],
        [20.0, 20.0, 30.0, 30.0],
    ],
    device="cuda",
)

scores = torch.tensor([0.9, 0.8, 0.7], device="cuda")

keep = nms(boxes, scores, 0.5)

print(f"NMS device: {keep.device}")
print(f"NMS result: {keep.cpu().tolist()}")

assert keep.is_cuda
assert keep.cpu().tolist() == [0, 2]


# ---------------------------------------------------------------------------
# torchvision image decoding
# ---------------------------------------------------------------------------

image = np.zeros((16, 24, 3), dtype=np.uint8)
image[:, :, 0] = 100
image[:, :, 1] = 150
image[:, :, 2] = 200

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    for fmt, suffix in [
        ("JPEG", ".jpg"),
        ("PNG", ".png"),
        ("WEBP", ".webp"),
    ]:
        path = tmpdir / f"test{suffix}"
        Image.fromarray(image).save(path, format=fmt)

        decoded = decode_image(path, mode="RGB")

        print(
            f"{fmt}: shape={tuple(decoded.shape)}, "
            f"dtype={decoded.dtype}, device={decoded.device}"
        )

        assert decoded.shape == (3, 16, 24)
        assert decoded.dtype == torch.uint8


# ---------------------------------------------------------------------------
# transforms v2 on CUDA
# ---------------------------------------------------------------------------

x = torch.rand(3, 32, 32, device="cuda")

transform = v2.Compose(
    [
        v2.Resize((24, 24)),
        v2.Normalize(
            mean=[0.5, 0.5, 0.5],
            std=[0.5, 0.5, 0.5],
        ),
    ]
)

y = transform(x)

print(f"Transform output: shape={tuple(y.shape)}, device={y.device}")

assert y.shape == (3, 24, 24)
assert y.is_cuda


print("== torchvision CUDA smoke test passed ==")
PY