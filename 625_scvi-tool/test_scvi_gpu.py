import argparse, sys, time, inspect

def die(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def make_synth(scvi, cells, genes):
    from scvi.data import synthetic_iid
    sig = inspect.signature(synthetic_iid)
    p = sig.parameters
    if "n_obs" in p and "n_vars" in p:
        return synthetic_iid(n_obs=cells, n_vars=genes)
    if "batch_size" in p and "n_genes" in p:
        return synthetic_iid(batch_size=cells, n_genes=genes, n_batches=1)
    kwargs = {}
    if "batch_size" in p: kwargs["batch_size"] = cells
    if "n_genes" in p: kwargs["n_genes"] = genes
    if "n_batches" in p: kwargs["n_batches"] = 1
    if not kwargs:
        die(f"Don't know how to call synthetic_iid; signature is {sig}")
    return synthetic_iid(**kwargs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-gpu", action="store_true")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--cells", type=int, default=256)
    ap.add_argument("--genes", type=int, default=200)
    args = ap.parse_args()

    import torch
    print("Python:", sys.version.split()[0])
    print("Torch:", torch.__version__)
    print("Torch CUDA build:", torch.version.cuda)
    print("cuDNN:", torch.backends.cudnn.version())
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA device count:", torch.cuda.device_count())

    if not torch.cuda.is_available():
        if args.require_gpu:
            die("torch.cuda.is_available() is False but --require-gpu was set")
        print("No GPU visible; exiting OK (no --require-gpu).")
        return 0

    if args.device >= torch.cuda.device_count():
        die(f"--device {args.device} >= device_count {torch.cuda.device_count()}")

    torch.cuda.set_device(args.device)
    dev = torch.device(f"cuda:{args.device}")
    print(f"Using device: {dev} ({torch.cuda.get_device_name(args.device)})")

    a = torch.randn(2048, 1024, device=dev)
    b = torch.randn(1024, 512, device=dev)
    torch.cuda.synchronize()
    t0 = time.time()
    _ = a @ b
    torch.cuda.synchronize()
    print("CUDA matmul OK")

    import scvi
    from scvi.model import SCVI

    print("scvi-tools:", scvi.__version__)
    scvi.settings.seed = 0

    adata = make_synth(scvi, args.cells, args.genes)
    SCVI.setup_anndata(adata)
    model = SCVI(adata, n_latent=5)

    model.train(
        max_epochs=args.epochs,
        accelerator="gpu",
        devices=[args.device],
        enable_progress_bar=False,
        logger=False,
        enable_checkpointing=False,
    )

    pdev = next(model.module.parameters()).device
    print("Model parameter device after training:", pdev)
    if pdev.type != "cuda":
        die(f"Expected model params on cuda, got {pdev}")

    print("OK: GPU works and scvi-tools trains on GPU.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
