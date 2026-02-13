import sys,random,torch,pytorch_lightning as pl
from cascadia.model import AugmentedSpec2Pep
from cascadia.depthcharge.tokenizers import PeptideTokenizer

def _make_tensors(dev,B=2,P=32,L=12,vocab=64):
  spectra=torch.zeros(B,P,4,device=dev,dtype=torch.float32)
  spectra[:,:,0]=100+1900*torch.rand(B,P,device=dev)
  spectra[:,:,1]=torch.rand(B,P,device=dev)
  spectra[:,:,2]=50*torch.rand(B,P,device=dev)
  spectra[:,:,3]=torch.randint(1,3,(B,P),device=dev).float()
  prec=torch.zeros(B,2,device=dev,dtype=torch.float32)
  prec[:,0]=400+1200*torch.rand(B,device=dev)
  prec[:,1]=torch.randint(1,6,(B,),device=dev).float()
  seq=torch.randint(1,max(2,vocab),(B,L),device=dev,dtype=torch.long)
  return spectra,prec,seq

def _call_training_step(m,batch,batch_idx=0):
  fn=m.training_step
  try: return fn(batch,batch_idx)
  except TypeError: return fn(batch)

def _pick_opt(cfg):
  if isinstance(cfg,(list,tuple)): cfg=cfg[0]
  if isinstance(cfg,dict): cfg=cfg.get("optimizer", cfg.get("opt", cfg.get("optimizers", None)))
  if isinstance(cfg,(list,tuple)): cfg=cfg[0]
  return cfg if hasattr(cfg,"step") else None

def _make_frag_labels_like_pred(pred_frag):
  dev=pred_frag.device
  if pred_frag.ndim==3:
    a,b,c=pred_frag.shape
    if c>1:
      return torch.zeros((a*b,),device=dev,dtype=torch.long), c, (a,b,c), "flattened (B*T,)"
    if b>1:
      return torch.zeros((a*c,),device=dev,dtype=torch.long), b, (a,b,c), "flattened (B*C,) [rare]"
    return torch.zeros((a,),device=dev,dtype=torch.long), 1, (a,b,c), "vector (B,) [degenerate]"
  if pred_frag.ndim==2:
    a,b=pred_frag.shape
    return torch.zeros((a,),device=dev,dtype=torch.long), b, (a,b), "vector (B,)"
  raise RuntimeError(f"Unsupported pred_frag shape: {tuple(pred_frag.shape)}")

def main():
  torch.manual_seed(0); random.seed(0)
  dev="cuda" if torch.cuda.is_available() else "cpu"
  print("python:", sys.version.split()[0])
  print("torch:", torch.__version__, "cuda:", torch.cuda.is_available())
  print("pytorch_lightning:", pl.__version__)
  if torch.cuda.is_available(): print("gpu:", torch.cuda.get_device_name(0))
  print("device:", dev)

  tok=PeptideTokenizer()
  vocab=len(tok) if hasattr(tok,"__len__") else 64
  print("tokenizer:", type(tok).__name__, "vocab:", vocab)

  m=AugmentedSpec2Pep(d_model=64,n_layers=1,rt_width=50.0,n_head=4,dropout=0.0,dim_feedforward=128,tokenizer=tok,max_charge=6).to(dev)
  m.log=lambda *a,**k: None

  spectra,prec,seq=_make_tensors(dev,vocab=vocab)

  m.eval()
  with torch.no_grad():
    preds,pred_prec,pred_frag=m._forward_step(spectra,prec,seq)
  print("forward: OK; pred_frag:", tuple(pred_frag.shape), pred_frag.dtype)

  frag_labels,nclass,shape,mode=_make_frag_labels_like_pred(pred_frag)
  print("frag_labels:", tuple(frag_labels.shape), frag_labels.dtype, "| mode:", mode, "| classes:", nclass)

  batch=(spectra,prec,seq,frag_labels,None)

  m.train()
  loss=_call_training_step(m,batch,0)
  if isinstance(loss,dict) and "loss" in loss: loss=loss["loss"]
  if not torch.is_tensor(loss): raise RuntimeError(f"training_step returned {type(loss)}")
  print("training_step: OK; loss tensor:", tuple(loss.shape))

  opt=_pick_opt(m.configure_optimizers())
  if opt is None:
    print("configure_optimizers: no optimizer detected; PASS (forward+training_step OK)")
    print("PASS")
    return 0

  opt.zero_grad(set_to_none=True)
  loss.backward()
  opt.step()
  print("backward/step: OK; loss:", float(loss.detach().cpu()))
  print("PASS")
  return 0

if __name__=="__main__":
  raise SystemExit(main())
