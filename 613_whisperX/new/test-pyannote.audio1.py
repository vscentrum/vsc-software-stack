#!/usr/bin/env python3
"""Smoke test for pyannote.audio 4.0.7.

Default mode is offline: imports, package versions, in-memory audio processing,
TorchCodec WAV decoding, resampling, cropping, and CUDA when available.

Optional real diarization:
    export HF_TOKEN=...
    python pyannote_audio_smoketest.py --audio meeting.wav --device cuda
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import math
import os
import platform
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any

import numpy as np
import torch


DEFAULT_MODEL = "pyannote/speaker-diarization-community-1"
EXPECTED_VERSIONS = {
    "pyannote-audio": "4.0.7",
    "torch": "2.9.1",
    "torchaudio": "2.9.1",
    "torchcodec": "0.9.1",
}

REQUIRED_IMPORTS = (
    "pyannote.audio",
    "pyannote.core",
    "pyannote.database",
    "pyannote.metrics",
    "pyannote.pipeline",
    "pyannoteai.sdk",
    "asteroid_filterbanks",
    "einops",
    "lightning",
    "opentelemetry.sdk",
    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "pytorch_metric_learning",
    "torch_audiomentations",
    "torchmetrics",
    "julius",
    "torch_pitch_shift",
)


class SmokeTestError(RuntimeError):
    pass


def log(message: str) -> None:
    print(f"[pyannote.audio smoke test] {message}", flush=True)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def distribution_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError as err:
        raise SmokeTestError(f"Distribution {name!r} is not installed.") from err


def check_imports() -> None:
    log("Checking required imports...")
    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as err:
            raise SmokeTestError(
                f"Import failed for {module_name!r}: {type(err).__name__}: {err}"
            ) from err
        log(f"  import {module_name}: OK")


def check_versions(strict: bool) -> None:
    log("Installed versions:")
    mismatches = []

    for distribution, expected in EXPECTED_VERSIONS.items():
        actual = distribution_version(distribution)
        log(f"  {distribution}: {actual}")
        if actual != expected:
            mismatches.append(f"{distribution}: expected {expected}, found {actual}")

    log(f"  Python: {platform.python_version()}")
    log(f"  PyTorch build CUDA: {torch.version.cuda}")

    if mismatches:
        message = "Version mismatch:\n  " + "\n  ".join(mismatches)
        if strict:
            raise SmokeTestError(message)
        log(f"WARNING: {message}")


def make_waveform(sample_rate: int = 48_000, duration: float = 2.0) -> torch.Tensor:
    num_samples = round(sample_rate * duration)
    time = torch.arange(num_samples, dtype=torch.float32) / sample_rate

    left = 0.20 * torch.sin(2.0 * math.pi * 220.0 * time)
    right = 0.10 * torch.sin(2.0 * math.pi * 440.0 * time)
    return torch.stack((left, right))


def write_pcm16_wave(path: Path, waveform: torch.Tensor, sample_rate: int) -> None:
    check(waveform.ndim == 2, "Generated waveform must be two-dimensional.")
    check(torch.isfinite(waveform).all().item(), "Generated waveform contains NaN or Inf.")

    pcm = (
        waveform.clamp(-1.0, 1.0)
        .mul(32767.0)
        .round()
        .to(torch.int16)
        .transpose(0, 1)
        .contiguous()
        .cpu()
        .numpy()
    )

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(waveform.shape[0])
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def check_audio_processing() -> None:
    from pyannote.audio import Audio
    from pyannote.core import Segment

    source_rate = 48_000
    target_rate = 16_000
    duration = 2.0
    waveform = make_waveform(sample_rate=source_rate, duration=duration)
    audio = Audio(sample_rate=target_rate, mono="downmix")

    log("Testing in-memory downmixing and resampling...")
    processed, sample_rate = audio(
        {
            "waveform": waveform,
            "sample_rate": source_rate,
            "uri": "synthetic-memory",
        }
    )
    expected_samples = round(duration * target_rate)

    check(sample_rate == target_rate, f"Expected {target_rate} Hz, got {sample_rate} Hz.")
    check(processed.shape == (1, expected_samples), f"Unexpected shape: {processed.shape}.")
    check(processed.dtype == torch.float32, f"Unexpected dtype: {processed.dtype}.")
    check(torch.isfinite(processed).all().item(), "Processed waveform contains NaN or Inf.")
    check(processed.abs().max().item() > 0.0, "Processed waveform is unexpectedly silent.")

    log("Testing in-memory cropping...")
    cropped, crop_rate = audio.crop(
        {
            "waveform": waveform,
            "sample_rate": source_rate,
            "uri": "synthetic-memory",
        },
        Segment(0.25, 0.75),
    )
    check(crop_rate == target_rate, f"Crop returned {crop_rate} Hz.")
    check(cropped.shape == (1, 8_000), f"Unexpected cropped shape: {cropped.shape}.")

    log("Testing TorchCodec WAV decoding and file cropping...")
    with tempfile.TemporaryDirectory(prefix="pyannote-audio-smoke-") as tmpdir:
        wav_path = Path(tmpdir) / "synthetic-stereo.wav"
        write_pcm16_wave(wav_path, waveform, source_rate)

        decoded, decoded_rate = audio(wav_path)
        check(decoded_rate == target_rate, f"File decode returned {decoded_rate} Hz.")
        check(decoded.shape == (1, expected_samples), f"Unexpected decoded shape: {decoded.shape}.")
        check(torch.isfinite(decoded).all().item(), "Decoded waveform contains NaN or Inf.")

        file_duration = audio.get_duration(wav_path)
        check(abs(file_duration - duration) < 0.01, f"Unexpected duration: {file_duration:.6f} s.")

        file_crop, file_crop_rate = audio.crop(wav_path, Segment(0.50, 1.00))
        check(file_crop_rate == target_rate, f"File crop returned {file_crop_rate} Hz.")
        check(file_crop.shape == (1, 8_000), f"Unexpected file crop shape: {file_crop.shape}.")

    log("Offline audio workflow: OK")


def check_cuda(require_cuda: bool) -> None:
    available = torch.cuda.is_available()
    log(f"CUDA available at runtime: {available}")

    if not available:
        if require_cuda:
            raise SmokeTestError("CUDA was required, but torch.cuda.is_available() is False.")
        log("CUDA test skipped because no CUDA device is visible.")
        return

    device = torch.device("cuda")
    properties = torch.cuda.get_device_properties(device)
    log(f"CUDA device: {properties.name}")
    log(f"CUDA capability: {properties.major}.{properties.minor}")

    left = torch.arange(256 * 128, dtype=torch.float32, device=device).reshape(256, 128)
    right = torch.ones((128, 32), dtype=torch.float32, device=device)
    result = left @ right
    torch.cuda.synchronize()

    check(result.shape == (256, 32), f"Unexpected CUDA result shape: {result.shape}.")
    check(torch.isfinite(result).all().item(), "CUDA result contains NaN or Inf.")
    log("CUDA tensor operation: OK")


def get_huggingface_token(explicit_token: str | None) -> str:
    token = explicit_token or os.environ.get("HF_TOKEN")
    token = token or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        raise SmokeTestError(
            "The real workflow needs --token, HF_TOKEN, or HUGGINGFACE_HUB_TOKEN."
        )
    return token


def select_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if requested == "cuda" and not torch.cuda.is_available():
        raise SmokeTestError("--device cuda was requested, but no CUDA device is visible.")

    return torch.device(requested)


def count_turns(annotation: Any) -> tuple[int, list[str]]:
    turns = list(annotation.itertracks(yield_label=True))
    labels = sorted({speaker for _, _, speaker in turns})
    return len(turns), labels


def run_real_diarization(args: argparse.Namespace) -> None:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation

    audio_path = Path(args.audio).expanduser().resolve()
    check(audio_path.is_file(), f"Audio file does not exist: {audio_path}")

    token = get_huggingface_token(args.token)
    device = select_device(args.device)

    log(f"Loading pipeline {args.model!r}...")
    pipeline = Pipeline.from_pretrained(
        args.model,
        token=token,
        cache_dir=args.cache_dir,
    )
    check(pipeline is not None, "Pipeline.from_pretrained returned None.")

    log(f"Moving pipeline to {device}...")
    pipeline.to(device)

    pipeline_kwargs = {}
    if args.num_speakers is not None:
        pipeline_kwargs["num_speakers"] = args.num_speakers

    log(f"Running diarization on {audio_path}...")
    output = pipeline(audio_path, **pipeline_kwargs)
    diarization = getattr(output, "speaker_diarization", output)
    check(isinstance(diarization, Annotation), "Pipeline did not return a pyannote Annotation.")

    num_turns, speakers = count_turns(diarization)
    log(f"Detected {len(speakers)} speaker(s) across {num_turns} turn(s).")

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"  {turn.start:8.3f}  {turn.end:8.3f}  {speaker}")

    exclusive = getattr(output, "exclusive_speaker_diarization", None)
    if exclusive is not None:
        check(
            isinstance(exclusive, Annotation),
            "exclusive_speaker_diarization is not a pyannote Annotation.",
        )
        exclusive_turns, _ = count_turns(exclusive)
        log(f"Exclusive diarization contains {exclusive_turns} turn(s).")

    embeddings = getattr(output, "speaker_embeddings", None)
    if embeddings is not None:
        check(isinstance(embeddings, np.ndarray), "Speaker embeddings are not a NumPy array.")
        check(embeddings.ndim == 2, f"Unexpected embedding shape: {embeddings.shape}.")
        check(
            embeddings.shape[0] == len(speakers),
            "The number of speaker embeddings does not match the number of speakers.",
        )
        check(np.isfinite(embeddings).all(), "Speaker embeddings contain NaN or Inf.")
        log(f"Speaker embedding shape: {embeddings.shape}")

    log("Real diarization workflow: OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audio",
        metavar="PATH",
        help="Run the real pretrained diarization workflow on this audio file.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Pipeline model identifier or local pipeline path (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--token",
        help="Hugging Face token. Prefer HF_TOKEN to avoid exposing it in process listings.",
    )
    parser.add_argument("--cache-dir", help="Optional Hugging Face model cache directory.")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device for the real pipeline workflow (default: auto).",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        help="Optional known number of speakers for the real workflow.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Fail when no usable CUDA device is visible.",
    )
    parser.add_argument(
        "--strict-versions",
        action="store_true",
        help="Fail unless package versions exactly match this EasyBuild stack.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("PYANNOTE_METRICS_ENABLED", "0")

    log(f"Python executable: {sys.executable}")
    check_imports()
    check_versions(strict=args.strict_versions)
    check_audio_processing()
    check_cuda(require_cuda=args.require_cuda)

    if args.audio:
        run_real_diarization(args)
    else:
        log("Real diarization workflow skipped; pass --audio PATH to enable it.")

    log("All requested checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeTestError as err:
        print(f"[pyannote.audio smoke test] FAILED: {err}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as err:
        print(
            f"[pyannote.audio smoke test] FAILED with {type(err).__name__}: {err}",
            file=sys.stderr,
        )
        raise
