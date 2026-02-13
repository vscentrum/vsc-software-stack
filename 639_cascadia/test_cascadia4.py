import io, torch
from cascadia.model import AugmentedSpec2Pep
from cascadia.depthcharge.tokenizers import PeptideTokenizer

dev="cuda" if torch.cuda.is_available() else "cpu"
m=AugmentedSpec2Pep(d_model=64,n_layers=1,rt_width=50.0,n_head=4,dropout=0.0,dim_feedforward=128,
                    tokenizer=PeptideTokenizer(),max_charge=6).to(dev)
b=io.BytesIO()
torch.save(m.state_dict(), b)
b.seek(0)
sd=torch.load(b, map_location="cpu")
m2=AugmentedSpec2Pep(d_model=64,n_layers=1,rt_width=50.0,n_head=4,dropout=0.0,dim_feedforward=128,
                     tokenizer=PeptideTokenizer(),max_charge=6)
m2.load_state_dict(sd, strict=True)
print("state_dict save/load PASS")
