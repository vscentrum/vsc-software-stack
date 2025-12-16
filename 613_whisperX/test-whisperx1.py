import argparse, os, sys, time, json, tempfile, wave
import numpy as np

def make_dummy_wav(path, sr=16000, seconds=4.0):
    t = np.arange(int(sr*seconds), dtype=np.float32)/sr
    x = 0.15*np.sin(2*np.pi*220*t) + 0.02*np.sin(2*np.pi*440*t) + 0.005*np.random.randn(t.size).astype(np.float32)
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", type=str, default=None, help="Path to audio file (wav/mp3/m4a/etc). If omitted, generates a dummy WAV.")
    ap.add_argument("--model", type=str, default="tiny", help="Whisper model size (tiny/base/small/medium/large-v3 etc).")
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--device", type=str, default=None, help="cuda/cpu (default: auto)")
    ap.add_argument("--compute_type", type=str, default=None, help="float16/int8/float32 (default: sensible auto)")
    ap.add_argument("--no_align", action="store_true")
    ap.add_argument("--diarize", action="store_true")
    ap.add_argument("--hf_token", type=str, default=os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN"))
    args = ap.parse_args()

    t0 = time.time()
    print("Python:", sys.version.replace("\n"," "))
    try:
        import torch
        import whisperx
    except Exception as e:
        print("\nIMPORT FAILED:\n", repr(e))
        raise

    print("torch:", torch.__version__)
    print("whisperx:", getattr(whisperx, "__version__", "unknown"))
    print("numpy:", np.__version__)
    try:
        import pandas as pd
        print("pandas:", pd.__version__)
    except Exception as e:
        print("pandas: import failed:", repr(e))

    cuda_ok = torch.cuda.is_available()
    if args.device is None:
        device = "cuda" if cuda_ok else "cpu"
    else:
        device = args.device

    print("\nDevice requested:", device)
    print("torch.cuda.is_available():", cuda_ok)
    if cuda_ok:
        try:
            print("CUDA runtime:", torch.version.cuda)
            print("cuDNN enabled:", torch.backends.cudnn.enabled)
            print("GPU:", torch.cuda.get_device_name(0))
            a = torch.randn(1024, 1024, device="cuda", dtype=torch.float16)
            b = (a @ a).float().mean().item()
            torch.cuda.synchronize()
            print("CUDA matmul test OK, mean:", b)
        except Exception as e:
            print("CUDA test FAILED:", repr(e))

    if args.compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"
    else:
        compute_type = args.compute_type
    print("compute_type:", compute_type)

    if args.audio:
        audio_path = args.audio
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        make_dummy_wav(tmp.name)
        audio_path = tmp.name
        print("\nNo --audio given; generated dummy audio:", audio_path)

    print("\nLoading audio via whisperx.load_audio (checks ffmpeg path too)...")
    audio = whisperx.load_audio(audio_path)
    if not isinstance(audio, np.ndarray):
        audio = np.array(audio)
    print("Audio dtype/shape:", audio.dtype, audio.shape, "min/max:", float(audio.min()), float(audio.max()))

    print("\nLoading ASR model:", args.model)
    asr = whisperx.load_model(args.model, device, compute_type=compute_type)
    print("Transcribing...")
    tr0 = time.time()
    result = asr.transcribe(audio, batch_size=args.batch_size)
    tr1 = time.time()
    print("Transcribe done in %.2fs" % (tr1-tr0))
    print("Detected language:", result.get("language"))
    segs = result.get("segments") or []
    print("Segments:", len(segs))
    if segs:
        print("First segment:", json.dumps(segs[0], ensure_ascii=False)[:500])
    else:
        print("WARNING: no segments produced (try real speech audio to validate alignment/diarization).")

    aligned = None
    if not args.no_align:
        lang = result.get("language") or "en"
        print("\nLoading alignment model for language:", lang)
        am0 = time.time()
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        am1 = time.time()
        print("Align model loaded in %.2fs" % (am1-am0))
        if segs:
            print("Aligning (word timestamps)...")
            al0 = time.time()
            aligned = whisperx.align(segs, align_model, metadata, audio, device, return_char_alignments=False)
            al1 = time.time()
            print("Align done in %.2fs" % (al1-al0))
            aseg = aligned.get("segments") or []
            words = (aseg[0].get("words") if aseg else None)
            print("Aligned segments:", len(aseg))
            if words:
                print("First aligned segment, first 5 words:", json.dumps(words[:5], ensure_ascii=False)[:800])
            else:
                print("WARNING: alignment produced no word list (often happens on silence/non-speech).")
        else:
            print("Skipping alignment because there are no ASR segments.")

    if args.diarize:
        print("\nDiarization requested.")
        if not args.hf_token:
            print("No HF token found. Set --hf_token or env HF_TOKEN/HUGGINGFACE_TOKEN. Skipping diarization.")
        else:
            try:
                print("Loading diarization pipeline...")
                diar = whisperx.DiarizationPipeline(use_auth_token=args.hf_token, device=device)
                print("Running diarization...")
                dz0 = time.time()
                diar_segments = diar(audio_path)
                dz1 = time.time()
                print("Diarization done in %.2fs" % (dz1-dz0))
                print("Diarization segments head:", str(diar_segments.head() if hasattr(diar_segments, "head") else diar_segments)[:800])
                if aligned is not None:
                    print("Assigning speakers to words...")
                    spk = whisperx.assign_word_speakers(diar_segments, aligned)
                    ssegs = spk.get("segments") or []
                    if ssegs:
                        print("First segment w/ speaker:", json.dumps(ssegs[0], ensure_ascii=False)[:800])
                    else:
                        print("WARNING: speaker assignment produced no segments.")
                else:
                    print("Run without --no_align to test speaker assignment onto word timestamps.")
            except Exception as e:
                print("DIARIZATION FAILED:", repr(e))

    if args.audio is None:
        try:
            os.unlink(audio_path)
        except Exception:
            pass

    print("\nOK: script finished in %.2fs" % (time.time()-t0))

if __name__ == "__main__":
    main()
