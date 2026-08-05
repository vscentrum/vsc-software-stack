import sys, os, tempfile, subprocess, traceback
import pyreadr
from pandas.testing import assert_frame_equal
import pandas as pd
def v(mod):
    try:
        m=__import__(mod); return getattr(m,"__version__", "unknown")
    except Exception: return "not importable"
def as_pandas(x):
    if hasattr(x,"to_pandas"): return x.to_pandas()
    if hasattr(x,"to_pandas_df"): return x.to_pandas_df()
    return x
fails=[]
def chk(name, fn):
    try:
        fn(); print(f"[OK] {name}")
    except Exception as e:
        fails.append((name,e,traceback.format_exc()))
        print(f"[FAIL] {name}: {e}")

print("== Versions ==")
for m in ["infercnvpy","gtfparse","polars","pyarrow","pyreadr","pandas","anndata","scanpy","pybiomart","requests_cache"]:
    print(f"{m}: {v(m)}")
print()

def test_pyreadr_basic():
    df = pd.DataFrame({"a":[1,2,3],"b":[0.1,0.2,0.3],"c":["x","y","z"]})
    with tempfile.TemporaryDirectory() as d:
        rds = os.path.join(d, "t.rds")
        rdata = os.path.join(d, "t.RData")

        pyreadr.write_rds(rds, df)
        out = pyreadr.read_r(rds)
        df2 = list(out.values())[0]
        assert_frame_equal(df2.reset_index(drop=True), df.reset_index(drop=True), check_dtype=False)

        pyreadr.write_rdata(rdata, df, df_name="df")
        out2 = pyreadr.read_r(rdata)
        df3 = out2["df"]
        assert_frame_equal(df3.reset_index(drop=True), df.reset_index(drop=True), check_dtype=False)

def test_pyreadr_linkage():
    import pyreadr
    so=os.path.join(os.path.dirname(pyreadr.__file__), "librdata"+next(f[f.find(".cpython"):] for f in os.listdir(os.path.dirname(pyreadr.__file__)) if f.startswith("librdata") and f.endswith(".so")))
    if not os.path.exists(so): so=getattr(__import__("pyreadr.librdata",fromlist=["__file__"]),"__file__",None)
    if not so or not os.path.exists(so): raise RuntimeError("could not locate pyreadr librdata .so")
    out=subprocess.check_output(["ldd", so], text=True, stderr=subprocess.STDOUT)
    need=["libz","libbz2","liblzma"]
    for n in need:
        if n not in out: raise RuntimeError(f"{n} not found in ldd output")
    if "EBROOTLIBICONV" in os.environ:
        if "libiconv" not in out: raise RuntimeError("libiconv not found in ldd output (expected with EBROOTLIBICONV)")
    print("pyreadr.librdata:", so)
    print("ldd snippet:\n" + "\n".join([l for l in out.splitlines() if any(k in l for k in ["iconv","libz","libbz2","liblzma"])][:12]))

def test_gtfparse_minimal():
    from gtfparse import read_gtf
    gtf = "\n".join([
        'chr1\tsrc\tgene\t100\t200\t.\t+\t.\tgene_id "GENE1"; gene_name "G1";',
        'chr1\tsrc\texon\t100\t120\t.\t+\t.\tgene_id "GENE1"; gene_name "G1"; transcript_id "T1"; exon_number "1";',
        'chr1\tsrc\tgene\t300\t400\t.\t-\t.\tgene_id "GENE2"; gene_name "G2";',
        'chr1\tsrc\texon\t380\t400\t.\t-\t.\tgene_id "GENE2"; gene_name "G2"; transcript_id "T2"; exon_number "1";',
    ])+"\n"
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,"t.gtf")
        open(p,"w").write(gtf)
        df=as_pandas(read_gtf(p))
        cols=set(getattr(df,"columns",[]))
        for c in ["seqname","feature","start","end","gene_id","gene_name"]:
            if c not in cols: raise RuntimeError(f"missing column {c} (have {sorted(list(cols))[:20]})")
        if len(df)==0: raise RuntimeError("gtfparse returned empty dataframe")

def test_infercnvpy_genepos_from_gtf():
    import numpy as np, pandas as pd
    from anndata import AnnData
    from infercnvpy.io._genepos import genomic_position_from_gtf
    gtf = "\n".join([
        'chr1\tsrc\tgene\t100\t200\t.\t+\t.\tgene_id "GENE1"; gene_name "G1";',
        'chr1\tsrc\tgene\t300\t400\t.\t-\t.\tgene_id "GENE2"; gene_name "G2";',
    ])+"\n"
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,"t.gtf"); open(p,"w").write(gtf)
        ad=AnnData(X=np.zeros((3,2)), var=pd.DataFrame(index=["G1","G2"]))
        gp=genomic_position_from_gtf(p, adata=ad, gtf_gene_id="gene_name", inplace=False)
        gp=as_pandas(gp)
        if gp is None: raise RuntimeError("genomic_position_from_gtf returned None")
        cols=set(getattr(gp,"columns",[]))
        if not {"chromosome","start","end"}.issubset(cols):
            raise RuntimeError(f"unexpected columns from genomic_position_from_gtf: {sorted(list(cols))}")
        if len(gp)==0: raise RuntimeError("genomic_position_from_gtf returned empty table")

def test_pybiomart_import_chain():
    import requests_cache, pybiomart
    assert hasattr(pybiomart, "Server")

chk("pyreadr import + read/write RDS/RData roundtrip", test_pyreadr_basic)
chk("pyreadr librdata linkage (ldd) sanity", test_pyreadr_linkage)
chk("gtfparse read_gtf minimal GTF", test_gtfparse_minimal)
chk("infercnvpy genomic_position_from_gtf (gtfparse integration)", test_infercnvpy_genepos_from_gtf)
chk("pybiomart import chain (requests_cache present)", test_pybiomart_import_chain)

print()
if fails:
    print("== FAILURES ==")
    for n,e,tb in fails:
        print(f"\n--- {n} ---\n{tb}")
    sys.exit(1)
print("All checks passed.")