#!/usr/bin/env python3
"""Smoke test for a CTranslate2 installation.

The default test is fully offline and does not require a model. It checks:

* Python package import and version
* CPU compute-type discovery
* CPU StorageView creation, conversion, and NumPy round-trip
* CUDA discovery and CPU -> CUDA -> CPU data transfer when a GPU is visible
* EasyBuild installation root and shared-library dependencies
* ct2-transformers-converter entry point
* Optional loading of an existing CTranslate2 model

Examples:
    python ctranslate2_smoketest.py
    python ctranslate2_smoketest.py --require-cuda
    python ctranslate2_smoketest.py --strict-version
    python ctranslate2_smoketest.py --model /path/to/ct2-model --device cuda
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence

import numpy as np


EXPECTED_VERSION = "4.8.1"


class SmokeTestError(RuntimeError):
    """Raised when a smoke-test check fails."""


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and return captured output."""
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def check(condition: bool, message: str) -> None:
    """Raise a clear error when a check fails."""
    if not condition:
        raise SmokeTestError(message)


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def check_python_package(strict_version: bool) -> object:
    print_section("Python package")

    import ctranslate2

    version = importlib.metadata.version("ctranslate2")
    print(f"version:       {version}")
    print(f"module:        {Path(ctranslate2.__file__).resolve()}")
    print(f"Python:        {sys.version.split()[0]}")

    if strict_version:
        check(
            version == EXPECTED_VERSION,
            f"Expected CTranslate2 {EXPECTED_VERSION}, found {version}",
        )
    elif version != EXPECTED_VERSION:
        print(
            f"WARNING: expected {EXPECTED_VERSION}, found {version}; "
            "use --strict-version to make this fatal"
        )

    required_api = (
        "Device",
        "StorageView",
        "get_cuda_device_count",
        "get_supported_compute_types",
    )
    missing = [name for name in required_api if not hasattr(ctranslate2, name)]
    check(not missing, f"Missing Python API members: {', '.join(missing)}")

    print("Python API:    OK")
    return ctranslate2


def check_cpu(ctranslate2: object) -> None:
    print_section("CPU backend")

    compute_types = set(ctranslate2.get_supported_compute_types("cpu"))
    print(f"compute types: {', '.join(sorted(compute_types))}")
    check("float32" in compute_types, "CPU float32 compute type is not available")

    array = np.arange(24, dtype=np.float32).reshape(4, 6)
    storage = ctranslate2.StorageView.from_array(array)

    check(storage.device == "cpu", f"Unexpected StorageView device: {storage.device}")
    check(tuple(storage.shape) == array.shape, f"Unexpected shape: {storage.shape}")

    roundtrip = np.asarray(storage)
    check(
        np.array_equal(roundtrip, array),
        "CPU StorageView did not preserve the input values",
    )

    converted = storage.to(ctranslate2.DataType.float16)
    print(f"converted dtype: {converted.dtype}")

    converted_back = converted.to(ctranslate2.DataType.float32)
    print(f"restored dtype:  {converted_back.dtype}")

    roundtrip_float32 = np.asarray(converted_back)
    check(
        np.allclose(roundtrip_float32, array),
        "StorageView float32 -> float16 -> float32 conversion failed",
    )

    print("StorageView:   OK")
    print("CPU backend:   OK")


def check_cuda(ctranslate2: object, require_cuda: bool) -> int:
    print_section("CUDA backend")

    device_count = int(ctranslate2.get_cuda_device_count())
    print(f"visible GPUs:  {device_count}")

    if device_count == 0:
        if require_cuda:
            raise SmokeTestError(
                "No CUDA device is visible, but --require-cuda was specified"
            )
        print("CUDA checks:   SKIPPED (no visible GPU)")
        return 0

    compute_types = set(ctranslate2.get_supported_compute_types("cuda", 0))
    print(f"compute types: {', '.join(sorted(compute_types))}")
    check("float32" in compute_types, "CUDA float32 compute type is not available")
    check("float16" in compute_types, "CUDA float16 compute type is not available")

    array = np.arange(32, dtype=np.float32).reshape(4, 8)
    cpu_storage = ctranslate2.StorageView.from_array(array)
    cuda_storage = cpu_storage.to_device(ctranslate2.Device.cuda)

    check(cuda_storage.device == "cuda", f"Unexpected CUDA device: {cuda_storage.device}")
    check(cuda_storage.device_index == 0, f"Unexpected device index: {cuda_storage.device_index}")

    returned = cuda_storage.to_device(ctranslate2.Device.cpu)
    roundtrip = np.asarray(returned)
    check(
        np.array_equal(roundtrip, array),
        "CPU -> CUDA -> CPU StorageView transfer changed the values",
    )

    print("CUDA transfer: OK")
    print("CUDA backend:  OK")
    return device_count


def find_install_root() -> Path | None:
    root = os.environ.get("EBROOTCTRANSLATE2")
    if not root:
        return None
    return Path(root).resolve()


def check_shared_library() -> None:
    print_section("Shared library")

    root = find_install_root()
    if root is None:
        print("EBROOTCTRANSLATE2 is not set; linkage inspection skipped")
        return

    library = root / "lib" / "libctranslate2.so"
    check(library.is_file(), f"Missing shared library: {library}")
    print(f"library:       {library}")

    ldd = shutil.which("ldd")
    if ldd is None:
        print("ldd is unavailable; linkage inspection skipped")
        return

    result = run_command([ldd, str(library)])
    check(result.returncode == 0, f"ldd failed:\n{result.stdout}")
    check("not found" not in result.stdout, f"Unresolved shared library:\n{result.stdout}")
    check(
        "libflexiblas.so" in result.stdout,
        "libctranslate2.so is not linked to FlexiBLAS",
    )

    print("dependencies:  resolved")
    print("FlexiBLAS:     linked")
    print("shared lib:    OK")


def check_converter_cli() -> None:
    print_section("Converter CLI")

    executable = shutil.which("ct2-transformers-converter")
    check(executable is not None, "ct2-transformers-converter is not on PATH")
    print(f"executable:    {Path(executable).resolve()}")

    result = run_command([executable, "--help"])
    check(
        result.returncode == 0,
        "ct2-transformers-converter --help failed:\n" + result.stdout,
    )
    check(
        "usage:" in result.stdout.lower(),
        "Converter help output did not contain a usage message",
    )

    print("converter CLI: OK")


def check_optional_model(
    ctranslate2: object,
    model_path: Path | None,
    model_kind: str,
    device: str,
    compute_type: str,
) -> None:
    if model_path is None:
        return

    print_section("Optional model load")

    check(model_path.is_dir(), f"Model directory does not exist: {model_path}")
    check(
        ctranslate2.contains_model(str(model_path)),
        f"Directory is not recognized as a CTranslate2 model: {model_path}",
    )

    if model_kind == "translator":
        model = ctranslate2.Translator(
            str(model_path),
            device=device,
            compute_type=compute_type,
            inter_threads=1,
            intra_threads=1,
        )
    elif model_kind == "generator":
        model = ctranslate2.Generator(
            str(model_path),
            device=device,
            compute_type=compute_type,
            inter_threads=1,
            intra_threads=1,
        )
    elif model_kind == "whisper":
        model = ctranslate2.models.Whisper(
            str(model_path),
            device=device,
            compute_type=compute_type,
        )
    else:
        raise SmokeTestError(f"Unsupported model kind: {model_kind}")

    check(model.model_is_loaded, "CTranslate2 model was not loaded")
    print(f"model:         {model_path}")
    print(f"kind:          {model_kind}")
    print(f"device:        {model.device}")
    print(f"compute type:  {model.compute_type}")
    print("model load:    OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run offline smoke tests for CTranslate2."
    )
    parser.add_argument(
        "--strict-version",
        action="store_true",
        help=f"fail unless the installed version is exactly {EXPECTED_VERSION}",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="fail when no CUDA device is visible",
    )
    parser.add_argument(
        "--model",
        type=Path,
        help="optionally load an existing CTranslate2 model directory",
    )
    parser.add_argument(
        "--model-kind",
        choices=("translator", "generator", "whisper"),
        default="translator",
        help="API used for --model (default: translator)",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="auto",
        help="device used for --model (default: auto)",
    )
    parser.add_argument(
        "--compute-type",
        default="auto",
        help="compute type used for --model (default: auto)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        ctranslate2 = check_python_package(args.strict_version)
        check_cpu(ctranslate2)
        check_cuda(ctranslate2, args.require_cuda)
        check_shared_library()
        check_converter_cli()
        check_optional_model(
            ctranslate2,
            args.model,
            args.model_kind,
            args.device,
            args.compute_type,
        )
    except (SmokeTestError, ImportError, OSError, RuntimeError) as error:
        print(f"\nSMOKE TEST FAILED: {error}", file=sys.stderr)
        return 1

    print("\n== CTranslate2 smoke test passed ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
