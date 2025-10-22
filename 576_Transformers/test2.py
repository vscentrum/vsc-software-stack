import sys, tempfile, traceback
import torch
from transformers import (
    BertConfig, BertForSequenceClassification, BertModel, BertForMaskedLM,
    AutoModelForCausalLM, AutoTokenizer, pipeline
)

def ok(msg): print("[OK]", msg)
def fail(msg, exc=None):
    print("[FAIL]", msg)
    if exc: traceback.print_exception(exc)
    sys.exit(1)

def tiny_forward_backward(device):
    cfg = BertConfig(vocab_size=101, hidden_size=64, num_hidden_layers=2,
                     num_attention_heads=2, intermediate_size=128, num_labels=3)
    m = BertForSequenceClassification(cfg).to(device).train()
    bs, seqlen = 4, 16
    x = torch.randint(0, cfg.vocab_size, (bs, seqlen), device=device)
    attn = torch.ones_like(x)
    labels = torch.randint(0, cfg.num_labels, (bs,), device=device)
    out = m(input_ids=x, attention_mask=attn, labels=labels)
    out.loss.backward()
    torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
    torch.optim.AdamW(m.parameters(), lr=1e-3).step()
    ok(f"forward/backward on {device}: loss={out.loss.item():.4f}")

def gen_pipeline(device):
    gen = pipeline("text-generation", model="sshleifer/tiny-gpt2",
                   device=(device if device=="cpu" else 0))  # pipeline expects -1/CPU or index for CUDA
    out = gen("Hello world,", max_new_tokens=8, do_sample=False)
    txt = out[0]["generated_text"]
    ok(f"text-generation on {device}: len={len(txt)} preview={txt[:50]!r}")

def feat_pipeline(device):
    fe = pipeline("feature-extraction",
                  model="sshleifer/tiny-distilroberta-base",
                  device=(device if device=="cpu" else 0))
    emb = fe("quick check", return_tensors=True)[0]
    ok(f"feature-extraction on {device}: shape={tuple(emb.shape)} dtype={getattr(emb,'dtype',type(emb))}")

def roundtrip_safetensors():
    mdl = "sshleifer/tiny-gpt2"
    tok = AutoTokenizer.from_pretrained(mdl)
    m = AutoModelForCausalLM.from_pretrained(mdl)
    tmp = tempfile.mkdtemp(prefix="hf_rt_")
    m.save_pretrained(tmp, safe_serialization=True)
    tok.save_pretrained(tmp)
    _ = AutoModelForCausalLM.from_pretrained(tmp)
    ok("save/load roundtrip with safetensors")

def torch_compile_sanity():
    if not hasattr(torch, "compile"):
        print("[SKIP] torch.compile not available")
        return
    m = BertModel(BertConfig(vocab_size=101, hidden_size=64, num_hidden_layers=1,
                             num_attention_heads=2, intermediate_size=128))
    m = torch.compile(m, mode="reduce-overhead")
    x = torch.randint(0,101,(2,8))
    with torch.no_grad(): y = m(x).last_hidden_state
    ok(f"torch.compile: out shape={tuple(y.shape)}")

def cuda_amp_sanity():
    if not torch.cuda.is_available():
        print("[SKIP] CUDA not available")
        return
    m = BertForMaskedLM(BertConfig(vocab_size=101, hidden_size=128, num_hidden_layers=2,
                                   num_attention_heads=2, intermediate_size=256)).cuda().eval()
    x = torch.randint(0,101,(2,16), device="cuda")
    with torch.cuda.amp.autocast(), torch.no_grad():
        y = m(input_ids=x).logits
    ok(f"CUDA amp: dtype={y.dtype} shape={tuple(y.shape)}")

def main():
    print("Torch", torch.__version__, "CUDA avail:", torch.cuda.is_available())
    # 1) pure PyTorch/Transformers forward+backward
    tiny_forward_backward("cpu")
    if torch.cuda.is_available(): tiny_forward_backward("cuda")

    # 2) pipelines (downloads once; set HF_HOME if needed)
    try:
        gen_pipeline("cpu")
        feat_pipeline("cpu")
        if torch.cuda.is_available():
            gen_pipeline("cuda")
            feat_pipeline("cuda")
    except Exception as e:
        # helpful hint if offline or no outbound net
        msg = "pipelines failed (possibly no network / proxy / SSL). " \
              "Pre-warm the cache or set HF_HOME and run once online."
        fail(msg, e)

    # 3) save/load roundtrip
    try:
        roundtrip_safetensors()
    except Exception as e:
        fail("safetensors save/load failed", e)

    # 4) optional extras
    torch_compile_sanity()
    cuda_amp_sanity()
    ok("ALL CHECKS PASSED")

if __name__ == "__main__":
    try: main()
    except Exception as e: fail("unexpected error", e)
