#!/usr/bin/env bash
set -euo pipefail

export PYTHONNOUSERSITE=1

echo "== CLI checks =="

command -v whisperx
command -v ffmpeg

whisperx -h >/dev/null
ffmpeg -version | head -n 1

python -s - <<'PY'
import math
import tempfile
import wave
from importlib.metadata import version
from pathlib import Path

import av
import ctranslate2
import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
import torchaudio
import torchcodec
import torchvision

import whisperx
from pyannote.audio.core.io import Audio
from torchcodec.decoders import AudioDecoder
from torchvision.ops import nms
from whisperx.audio import load_audio, log_mel_spectrogram
from whisperx.diarize import assign_word_speakers
from whisperx.vads.pyannote import Pyannote


def print_version(dist):
    try:
        print(f"{dist:20s}: {version(dist)}")
    except Exception as err:
        raise RuntimeError(f"Could not determine version of {dist}") from err


print("\n== Package versions ==")

for dist in [
    "whisperx",
    "torch",
    "torchaudio",
    "torchvision",
    "torchcodec",
    "ctranslate2",
    "faster-whisper",
    "onnxruntime",
    "av",
    "pyannote-audio",
    "transformers",
    "huggingface-hub",
    "tokenizers",
    "omegaconf",
    "nltk",
    "tqdm",
]:
    print_version(dist)

assert version("whisperx") == "3.8.6"
assert version("torch").split("+")[0] == "2.9.1"
assert version("torchaudio").split("+")[0] == "2.9.1"
assert version("torchvision") == "0.24.1"

print("\n== PyTorch CUDA ==")

print(f"PyTorch CUDA: {torch.version.cuda}")
assert torch.version.cuda == "12.8"
assert torch.cuda.is_available()

print(f"GPU: {torch.cuda.get_device_name(0)}")

a = torch.tensor(
    [[1.0, 2.0], [3.0, 4.0]],
    device="cuda",
)
b = a @ a
torch.cuda.synchronize()

expected = torch.tensor(
    [[7.0, 10.0], [15.0, 22.0]],
    device="cuda",
)
torch.testing.assert_close(b, expected)

print("PyTorch CUDA computation: OK")


print("\n== CTranslate2 CUDA ==")

cuda_devices = ctranslate2.get_cuda_device_count()
compute_types = ctranslate2.get_supported_compute_types("cuda")

print(f"CTranslate2 CUDA devices: {cuda_devices}")
print(f"CTranslate2 CUDA compute types: {sorted(compute_types)}")

assert cuda_devices > 0
assert "float16" in compute_types

print("CTranslate2 CUDA: OK")


print("\n== ONNX Runtime CUDA ==")

providers = ort.get_available_providers()
print(f"ONNX Runtime providers: {providers}")

assert "CUDAExecutionProvider" in providers

print("ONNX Runtime CUDA provider: OK")


print("\n== torchvision CUDA extension ==")

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

print(f"NMS result: {keep.cpu().tolist()}")
assert keep.is_cuda
assert keep.cpu().tolist() == [0, 2]

print("torchvision CUDA operator: OK")


print("\n== Create synthetic audio ==")

with tempfile.TemporaryDirectory() as tmpdir:
    path = Path(tmpdir) / "test.wav"

    source_rate = 22050
    duration = 1.0
    frames = int(source_rate * duration)

    t = np.arange(frames, dtype=np.float64) / source_rate

    left = 0.2 * np.sin(2.0 * math.pi * 440.0 * t)
    right = 0.2 * np.sin(2.0 * math.pi * 660.0 * t)

    stereo = np.column_stack((left, right))
    pcm = np.clip(stereo * 32767.0, -32768, 32767).astype("<i2")

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(source_rate)
        wav.writeframes(pcm.tobytes())

    assert path.is_file()
    print(f"Created: {path}")


    print("\n== WhisperX FFmpeg audio loader ==")

    audio = load_audio(str(path))

    print(f"dtype: {audio.dtype}")
    print(f"shape: {audio.shape}")

    assert audio.dtype == np.float32
    assert abs(audio.shape[0] - 16000) <= 2
    assert np.isfinite(audio).all()

    print("WhisperX load_audio: OK")


    print("\n== WhisperX CUDA mel spectrogram ==")

    mel = log_mel_spectrogram(
        audio,
        n_mels=80,
        device="cuda",
    )

    print(f"Mel shape: {tuple(mel.shape)}")
    print(f"Mel device: {mel.device}")

    assert mel.is_cuda
    assert mel.shape[0] == 80
    assert torch.isfinite(mel).all()

    print("WhisperX CUDA mel spectrogram: OK")


    print("\n== PyAV decoding ==")

    with av.open(str(path)) as container:
        decoded = list(container.decode(audio=0))

    print(f"PyAV decoded frames: {len(decoded)}")
    assert decoded

    print("PyAV/FFmpeg: OK")


    print("\n== TorchCodec decoding ==")

    decoder = AudioDecoder(
        str(path),
        sample_rate=16000,
        num_channels=1,
    )
    samples = decoder.get_all_samples()

    print(f"TorchCodec sample rate: {samples.sample_rate}")
    print(f"TorchCodec shape: {tuple(samples.data.shape)}")

    assert samples.sample_rate == 16000
    assert samples.data.shape[0] == 1
    assert abs(samples.data.shape[1] - 16000) <= 2
    assert torch.isfinite(samples.data).all()

    print("TorchCodec: OK")


    print("\n== pyannote.audio decoding/resampling ==")

    pyannote_audio = Audio(
        sample_rate=16000,
        mono="downmix",
    )

    waveform, sample_rate = pyannote_audio(str(path))

    print(f"pyannote sample rate: {sample_rate}")
    print(f"pyannote waveform: {tuple(waveform.shape)}")

    assert sample_rate == 16000
    assert waveform.shape[0] == 1
    assert abs(waveform.shape[1] - 16000) <= 2
    assert torch.isfinite(waveform).all()

    print("pyannote.audio + TorchCodec + Torchaudio: OK")


    print("\n== Torchaudio resampling ==")

    resampled = torchaudio.functional.resample(
        waveform,
        16000,
        8000,
    )

    print(f"Resampled shape: {tuple(resampled.shape)}")

    assert resampled.shape[0] == 1
    assert abs(resampled.shape[1] - 8000) <= 2

    print("Torchaudio: OK")


    print("\n== WhisperX bundled Pyannote VAD ==")

    vad = Pyannote(
        torch.device("cuda"),
        chunk_size=30,
        vad_onset=0.5,
        vad_offset=0.363,
    )

    vad_input = {
        "waveform": Pyannote.preprocess_audio(audio),
        "sample_rate": 16000,
    }

    vad_output = vad(vad_input)

    print(f"VAD output type: {type(vad_output).__name__}")
    assert vad_output is not None

    print("WhisperX Pyannote VAD CUDA inference: OK")


print("\n== WhisperX ASR/alignment/diarization imports ==")

from whisperx.alignment import align, load_align_model
from whisperx.asr import FasterWhisperPipeline, WhisperModel, load_model
from whisperx.diarize import DiarizationPipeline

assert callable(load_model)
assert callable(load_align_model)
assert callable(align)
assert callable(DiarizationPipeline)

print("ASR imports: OK")
print("Alignment imports: OK")
print("Diarization imports: OK")


print("\n== WhisperX speaker assignment ==")

diarization = pd.DataFrame(
    {
        "start": [0.0, 1.0],
        "end": [1.0, 2.0],
        "speaker": ["SPEAKER_00", "SPEAKER_01"],
    }
)

transcript = {
    "segments": [
        {
            "start": 0.1,
            "end": 0.9,
            "text": "hello",
            "words": [
                {
                    "word": "hello",
                    "start": 0.1,
                    "end": 0.9,
                    "score": 1.0,
                }
            ],
        },
        {
            "start": 1.1,
            "end": 1.9,
            "text": "world",
            "words": [
                {
                    "word": "world",
                    "start": 1.1,
                    "end": 1.9,
                    "score": 1.0,
                }
            ],
        },
    ],
    "language": "en",
}

result = assign_word_speakers(diarization, transcript)

assert result["segments"][0]["speaker"] == "SPEAKER_00"
assert result["segments"][1]["speaker"] == "SPEAKER_01"
assert result["segments"][0]["words"][0]["speaker"] == "SPEAKER_00"
assert result["segments"][1]["words"][0]["speaker"] == "SPEAKER_01"

print("Speaker assignment: OK")


print("\n== Dependency coexistence ==")

import faster_whisper
import nltk
import omegaconf
import pyannote.audio
import tokenizers
import transformers
from huggingface_hub import HfApi

print("faster-whisper: OK")
print("Transformers: OK")
print("pyannote.audio: OK")
print("NLTK: OK")
print("OmegaConf: OK")
print("Hugging Face Hub: OK")
print("tokenizers: OK")


print("\n========================================")
print("== WhisperX CUDA smoke test passed ==")
print("========================================")
PY

python -m pip check

echo "== pip check passed =="