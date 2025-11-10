import json, os, platform, shutil, subprocess, sys, tempfile
import graphviz
print(json.dumps({"python":sys.version.split()[0],"platform":platform.platform(),"graphviz_py":graphviz.__version__}))
bins=["dot","neato","sfdp","fdp","twopi","circo","osage","patchwork"]
info={}
for b in bins:
    p=shutil.which(b)
    if p:
        r=subprocess.run([b,"-V"],capture_output=True,text=True)
        info[b]={"path":p,"version":(r.stdout or r.stderr).strip()}
    else:
        info[b]=None
print(json.dumps({"executables":info},indent=2))

if shutil.which("dot"):
    d=tempfile.mkdtemp(prefix="gv_")
    out=os.path.join(d,"probe.svg")
    r=subprocess.run(["dot","-Tsvg","-o",out],input="digraph{a->b}",text=True,capture_output=True)
    print(json.dumps({"svg_probe":{"path":out,"returncode":r.returncode,"stderr":r.stderr.strip()}}))
