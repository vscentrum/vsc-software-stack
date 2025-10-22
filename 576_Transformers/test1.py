import torch, os, tempfile
from transformers import BertConfig, BertForSequenceClassification, AutoModelForCausalLM, AutoTokenizer, pipeline, BertModel, BertForMaskedLM
def run(device):
    cfg = BertConfig(
        vocab_size=101, hidden_size=64, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=128, num_labels=3
    )
    m = BertForSequenceClassification(cfg).to(device)
    m.train()
    bs, seqlen = 4, 16
    x = torch.randint(0, cfg.vocab_size, (bs, seqlen), device=device)
    attn = torch.ones_like(x)
    labels = torch.randint(0, cfg.num_labels, (bs,), device=device)
    out = m(input_ids=x, attention_mask=attn, labels=labels)
    out.loss.backward()
    torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
    torch.optim.AdamW(m.parameters(), lr=1e-3).step()
    print(f"[{device}] loss={out.loss.item():.4f}")
run("cpu")
if torch.cuda.is_available():
    torch.set_default_device("cuda")
    run("cuda")
    
for device in (["cpu"] + (["cuda:0"] if torch.cuda.is_available() else [])):
    gen = pipeline("text-generation", model="sshleifer/tiny-gpt2", device=device)
    out = gen("Hello world,", max_new_tokens=8, do_sample=False)
    txt = out[0]["generated_text"]
    print(f"[{device}] OK; len={len(txt)}; preview={txt[:60]!r}")
    
fe = pipeline("feature-extraction", model="sshleifer/tiny-distilroberta-base", device=("cuda:0" if torch.cuda.is_available() else "cpu"))
emb = fe("quick check", return_tensors=True)
arr = emb[0]
print("shape:", arr.shape, "dtype:", arr.dtype, "mean:", float(arr.mean()))

mdl = "sshleifer/tiny-gpt2"
tok = AutoTokenizer.from_pretrained(mdl)
m = AutoModelForCausalLM.from_pretrained(mdl)
tmp = tempfile.mkdtemp(prefix="hf_rt_")
m.save_pretrained(tmp, safe_serialization=True)
tok.save_pretrained(tmp)
m2 = AutoModelForCausalLM.from_pretrained(tmp)
print("roundtrip OK; params:", sum(p.numel() for p in m2.parameters()))
if torch.cuda.is_available():
    m2.cuda().eval()
    ids = tok("hi", return_tensors="pt").to("cuda")
    with torch.no_grad(): _ = m2(**ids)
    print("CUDA forward OK")

if not hasattr(torch, "compile"): 
    print("torch.compile not available"); raise SystemExit(0)
m = BertModel(BertConfig(vocab_size=101, hidden_size=64, num_hidden_layers=1, num_attention_heads=2, intermediate_size=128))
m = torch.compile(m, mode="reduce-overhead")
x = torch.randint(0,101,(2,8))
with torch.no_grad(): y = m(x).last_hidden_state
print("compile OK; out:", tuple(y.shape))

if not torch.cuda.is_available(): 
    print("skip (no CUDA)"); raise SystemExit(0)
m = BertForMaskedLM(BertConfig(vocab_size=101, hidden_size=128, num_hidden_layers=2, num_attention_heads=2, intermediate_size=256)).cuda().eval()
x = torch.randint(0,101,(2,16), device="cuda")
with torch.cuda.amp.autocast(), torch.no_grad():
    y = m(input_ids=x).logits
print("amp OK; dtype:", y.dtype, "shape:", tuple(y.shape))