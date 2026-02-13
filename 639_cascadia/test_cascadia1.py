import sys, torch, pytorch_lightning as pl
from cascadia.model import AugmentedPeakEncoder, SpectrumTransformerEncoder

def main():
    print("== Versions ==")
    print("python:", sys.version.split()[0])
    print("torch:", torch.__version__)
    print("pytorch_lightning:", pl.__version__)
    print("cuda:", torch.cuda.is_available())

    dev = "cuda" if torch.cuda.is_available() else "cpu"

    d_model=64; n_head=4; n_layers=2; dim_ff=128; dropout=0.0
    peak = AugmentedPeakEncoder(d_model=d_model, max_rt_wavelength=120.0).to(dev)

    enc = SpectrumTransformerEncoder(
        d_model=d_model, n_head=n_head, n_layers=n_layers,
        dropout=dropout, dim_feedforward=dim_ff, peak_encoder=peak
    ).to(dev)

    B,P=2,32
    spectra = torch.zeros((B,P,4), device=dev, dtype=torch.float32)
    spectra[:,:,0] = 100 + 1900*torch.rand(B,P, device=dev)      # m/z
    spectra[:,:,1] = torch.rand(B,P, device=dev)                 # intensity in [0,1]
    spectra[:,:,2] = 60*torch.rand(B,P, device=dev)              # RT
    spectra[:,:,3] = torch.randint(1,3,(B,P), device=dev).float()# ms level 1/2

    with torch.no_grad():
        out = enc(spectra)

    print("\n== SpectrumTransformerEncoder output ==")
    if isinstance(out, (tuple, list)):
        print("tuple len:", len(out))
        for i,x in enumerate(out):
            if torch.is_tensor(x): print(f"[{i}] {tuple(x.shape)} {x.dtype} {x.device}")
            else: print(f"[{i}] {type(x)}")
    else:
        print("tensor:", tuple(out.shape), out.dtype, out.device)

    print("\nPASS")

if __name__ == "__main__":
    main()
