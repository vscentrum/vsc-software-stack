#!/usr/bin/env python3
import argparse, importlib, importlib.metadata, os, tempfile
from pathlib import Path

def ok(msg): print(f"[OK] {msg}")
def die(msg): raise RuntimeError(msg)

def check_imports():
    packages = {
        "geneformer":"geneformer", "anndata":"anndata", "bitsandbytes":"bitsandbytes",
        "datasets":"datasets", "loompy":"loompy", "matplotlib":"matplotlib", "numpy":"numpy",
        "optuna":"optuna", "optuna-integration":"optuna_integration", "packaging":"packaging",
        "pandas":"pandas", "peft":"peft", "pyarrow":"pyarrow", "pytz":"pytz", "ray":"ray",
        "scanpy":"scanpy", "scikit-learn":"sklearn", "scipy":"scipy", "seaborn":"seaborn",
        "setuptools":"setuptools", "statsmodels":"statsmodels", "tdigest":"tdigest",
        "tensorboard":"tensorboard", "torch":"torch", "tqdm":"tqdm",
        "transformers":"transformers", "accelerate":"accelerate",
    }
    for dist, mod in packages.items():
        importlib.import_module(mod)
        try: version = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError: version = "unknown"
        ok(f"{dist} {version}")

def check_geneformer_files():
    import geneformer
    paths = [
        geneformer.GENE_MEDIAN_FILE, geneformer.TOKEN_DICTIONARY_FILE,
        geneformer.ENSEMBL_DICTIONARY_FILE, geneformer.ENSEMBL_MAPPING_FILE,
        geneformer.GENE_MEDIAN_FILE_30M, geneformer.TOKEN_DICTIONARY_FILE_30M,
        geneformer.ENSEMBL_DICTIONARY_FILE_30M, geneformer.ENSEMBL_MAPPING_FILE_30M,
    ]
    for p in paths:
        p = Path(p)
        if not p.is_file() or p.stat().st_size == 0: die(f"Missing Geneformer data file: {p}")
    ok("V1/V2 Geneformer dictionaries are installed")

def make_tokenized_dataset(tmp):
    import anndata as ad
    import numpy as np
    import pandas as pd
    from datasets import load_from_disk
    from geneformer import TranscriptomeTokenizer
    from scipy import sparse

    tk = TranscriptomeTokenizer(model_version="V2", nproc=1)
    if "<cls>" not in tk.gene_token_dict or "<eos>" not in tk.gene_token_dict:
        die("V2 token dictionary lacks <cls>/<eos>")
    genes = [
        k for k in tk.gene_token_dict
        if k in tk.gene_median_dict and tk.gene_mapping_dict.get(k) == k
    ][:32]
    if len(genes) < 8: die("Could not find enough canonical V2 genes for tokenizer test")
    rng = np.random.default_rng(42)
    x = rng.integers(1, 50, size=(3, len(genes)), dtype=np.int32)
    obs = pd.DataFrame({"n_counts": x.sum(axis=1)}, index=[f"cell{i}" for i in range(3)])
    var = pd.DataFrame({"ensembl_id": genes}, index=genes)
    adata = ad.AnnData(X=sparse.csr_matrix(x), obs=obs, var=var)
    input_dir, output_dir = Path(tmp)/"input", Path(tmp)/"output"
    input_dir.mkdir(); output_dir.mkdir()
    adata.write_h5ad(input_dir/"smoke.h5ad")
    tk.tokenize_data(input_dir, output_dir, "smoke", file_format="h5ad")
    ds = load_from_disk(str(output_dir/"smoke.dataset"))
    if len(ds) != 3: die(f"Tokenizer produced {len(ds)} cells instead of 3")
    cls_id, eos_id = tk.gene_token_dict["<cls>"], tk.gene_token_dict["<eos>"]
    for row in ds:
        if row["length"] < 3: die("Tokenized cell is unexpectedly short")
        if row["input_ids"][0] != cls_id or row["input_ids"][-1] != eos_id:
            die("V2 tokenizer did not add expected <cls>/<eos> tokens")
    ok(f"TranscriptomeTokenizer converted synthetic h5ad to HF Dataset ({len(ds)} cells)")
    return ds, tk

def check_torch_transformers(ds, tk, require_cuda):
    import torch
    from transformers import BertConfig, BertForMaskedLM

    cuda = torch.cuda.is_available()
    print(f"[INFO] PyTorch {torch.__version__}, built for CUDA {torch.version.cuda}, CUDA available: {cuda}")
    if require_cuda and not cuda: die("--require-cuda requested but no CUDA device is available")
    device = torch.device("cuda" if cuda else "cpu")
    if cuda: ok(f"CUDA device: {torch.cuda.get_device_name(0)}")
    vocab_size = max(tk.gene_token_dict.values()) + 1
    cfg = BertConfig(vocab_size=vocab_size, hidden_size=32, num_hidden_layers=1,
                     num_attention_heads=4, intermediate_size=64, max_position_embeddings=4096,
                     pad_token_id=0)
    model = BertForMaskedLM(cfg).to(device).eval()
    ids = torch.tensor(ds[0]["input_ids"], dtype=torch.long, device=device).unsqueeze(0)
    with torch.no_grad(): out = model(input_ids=ids)
    if out.logits.shape[:2] != ids.shape: die(f"Unexpected Transformers output shape {out.logits.shape}")
    if not torch.isfinite(out.logits).all(): die("Non-finite values from Transformers forward pass")
    ok(f"PyTorch + Transformers BERT forward pass on {device.type}")
    return cuda

def check_bitsandbytes(cuda):
    import bitsandbytes as bnb
    if not cuda:
        print("[SKIP] bitsandbytes CUDA kernel test: no GPU visible")
        return
    import torch
    layer = bnb.nn.Linear8bitLt(16, 8, has_fp16_weights=False).cuda()
    x = torch.randn(4, 16, device="cuda", dtype=torch.float16)
    with torch.no_grad(): y = layer(x)
    if y.shape != (4, 8) or not torch.isfinite(y).all(): die("bitsandbytes Linear8bitLt CUDA test failed")
    ok("bitsandbytes Linear8bitLt CUDA kernel")

def check_real_model(model_dir):
    if model_dir is None:
        print("[SKIP] real Geneformer weights: pass --model-dir /path/to/Geneformer-V1-10M or Geneformer-V2-*")
        return
    import torch
    from geneformer import TranscriptomeTokenizer
    from transformers import AutoConfig, AutoModelForMaskedLM

    p = Path(model_dir)
    if not p.is_dir(): die(f"Model directory does not exist: {p}")
    cfg = AutoConfig.from_pretrained(str(p), local_files_only=True)
    version = "V1" if getattr(cfg, "max_position_embeddings", 4096) <= 2048 else "V2"
    tk = TranscriptomeTokenizer(model_version=version, nproc=1)
    vals = [v for k, v in tk.gene_token_dict.items() if not k.startswith("<")][:16]
    if version == "V2":
        vals = [tk.gene_token_dict["<cls>"]] + vals + [tk.gene_token_dict["<eos>"]]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoModelForMaskedLM.from_pretrained(str(p), local_files_only=True).to(device).eval()
    ids = torch.tensor([vals], dtype=torch.long, device=device)
    with torch.no_grad(): out = model(input_ids=ids)
    if out.logits.shape[:2] != ids.shape or not torch.isfinite(out.logits).all():
        die("Real Geneformer model forward pass failed")
    ok(f"real {version} Geneformer pretrained model loaded and ran on {device.type}: {p}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-cuda", action="store_true")
    ap.add_argument("--model-dir")
    args = ap.parse_args()
    print("=== Geneformer smoke test ===")
    check_imports()
    check_geneformer_files()
    with tempfile.TemporaryDirectory(prefix="geneformer-smoke-") as tmp:
        ds, tk = make_tokenized_dataset(tmp)
        cuda = check_torch_transformers(ds, tk, args.require_cuda)
        check_bitsandbytes(cuda)
    check_real_model(args.model_dir)
    print("=== ALL REQUESTED TESTS PASSED ===")

if __name__ == "__main__":
    main()
