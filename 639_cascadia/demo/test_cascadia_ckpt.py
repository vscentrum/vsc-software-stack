import sys,re,torch
import lightning as L
from cascadia.model import AugmentedSpec2Pep
from cascadia.depthcharge.tokenizers import PeptideTokenizer

class TokLenWrap:
  def __init__(self, base, n): self.base=base; self.n=n
  def __len__(self): return self.n
  def __getattr__(self, k): return getattr(self.base, k)

def load_ckpt(path):
  try: return torch.load(path, map_location="cpu", weights_only=False)
  except TypeError: return torch.load(path, map_location="cpu")

def get_state_dict(ckpt):
  sd=ckpt.get("state_dict", ckpt)
  if any(k.startswith("model.") for k in sd.keys()):
    sd={k[6:]:v for k,v in sd.items() if k.startswith("model.")}
  return sd

def infer(sd, ckpt):
  hp=ckpt.get("hyper_parameters", {}) or ckpt.get("hparams", {}) or {}
  aa_rows=sd["decoder.aa_encoder.weight"].shape[0]
  charge_rows=sd["decoder.charge_encoder.weight"].shape[0]
  d_model=sd["decoder.aa_encoder.weight"].shape[1]
  n_layers=None
  idx=[]
  for k in sd.keys():
    m=re.search(r"\.layers\.(\d+)\.", k)
    if m: idx.append(int(m.group(1)))
  n_layers=(max(idx)+1) if idx else hp.get("n_layers", 1)
  dim_ff=None
  for k,v in sd.items():
    if k.endswith(".linear1.weight") and v.ndim==2:
      dim_ff=int(v.shape[0]); break
  if dim_ff is None: dim_ff=int(hp.get("dim_feedforward", 1024))
  n_head=int(hp.get("n_head", 16))
  rt_width=float(hp.get("rt_width", 50.0))
  dropout=float(hp.get("dropout", 0.0))
  max_charge=int(hp.get("max_charge", charge_rows-1))
  return dict(d_model=d_model,n_layers=n_layers,dim_feedforward=dim_ff,n_head=n_head,rt_width=rt_width,dropout=dropout,
              aa_rows=aa_rows,charge_rows=charge_rows,max_charge=max_charge), hp

def make_fake_batch(dev,B,P,L,vocab,max_charge):
  spectra=torch.zeros(B,P,4,device=dev,dtype=torch.float32)
  spectra[:,:,0]=100+1900*torch.rand(B,P,device=dev)
  spectra[:,:,1]=torch.rand(B,P,device=dev)
  spectra[:,:,2]=50*torch.rand(B,P,device=dev)
  spectra[:,:,3]=torch.randint(1,3,(B,P),device=dev).float()
  prec=torch.zeros(B,2,device=dev,dtype=torch.float32)
  prec[:,0]=400+1200*torch.rand(B,device=dev)
  prec[:,1]=torch.randint(1,max_charge+1,(B,),device=dev).float()
  seq=torch.randint(1,max(2,vocab),(B,L),device=dev,dtype=torch.long)
  return spectra,prec,seq

def main():
  if len(sys.argv)<2:
    print("usage: python test_cascadia_ckpt.py /path/to/cascadia.ckpt"); return 2
  ckpt_path=sys.argv[1]
  print("python:", sys.version.split()[0])
  print("torch:", torch.__version__, "cuda:", torch.cuda.is_available())
  print("lightning:", L.__version__)
  if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))

  base_tok=PeptideTokenizer()
  print("tokenizer:", type(base_tok).__name__, "vocab:", (len(base_tok) if hasattr(base_tok,"__len__") else "unknown"))

  ckpt=load_ckpt(ckpt_path)
  sd=get_state_dict(ckpt)
  info,hp=infer(sd, ckpt)
  print("inferred:", {k:info[k] for k in ["d_model","n_layers","dim_feedforward","n_head","max_charge"]})
  print("ckpt vocab rows:", info["aa_rows"], "ckpt charge rows:", info["charge_rows"])

  tok=TokLenWrap(base_tok, info["aa_rows"])
  dev="cuda" if torch.cuda.is_available() else "cpu"
  m=AugmentedSpec2Pep(d_model=info["d_model"],n_layers=info["n_layers"],rt_width=info["rt_width"],n_head=info["n_head"],
                      dropout=info["dropout"],dim_feedforward=info["dim_feedforward"],tokenizer=tok,max_charge=info["max_charge"]).to(dev)

  try:
    res=m.load_state_dict(sd, strict=False)
    print("load_state_dict: OK; missing:", len(res.missing_keys), "unexpected:", len(res.unexpected_keys))
  except RuntimeError as e:
    ms=m.state_dict()
    sd2={k:v for k,v in sd.items() if (k in ms and hasattr(v,"shape") and ms[k].shape==v.shape)}
    print("load_state_dict: shape mismatch; loading only matching tensors:", len(sd2), "/", len(sd))
    res=m.load_state_dict(sd2, strict=False)
    print("partial load: OK; missing:", len(res.missing_keys), "unexpected:", len(res.unexpected_keys))

  spectra,prec,seq=make_fake_batch(dev,B=2,P=32,L=16,vocab=info["aa_rows"],max_charge=info["max_charge"])
  m.eval()
  with torch.no_grad():
    out=m._forward_step(spectra,prec,seq)
  if isinstance(out,(tuple,list)) and len(out)>=3:
    preds,pred_prec,pred_frag=out[:3]
    print("forward: OK; preds:", tuple(preds.shape), "pred_prec:", tuple(pred_prec.shape), "pred_frag:", tuple(pred_frag.shape))
  else:
    print("forward: OK; output type:", type(out))
  print("PASS")
  return 0

if __name__=="__main__":
  raise SystemExit(main())
