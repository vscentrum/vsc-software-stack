
import os, shutil, subprocess, sys, textwrap

def which_run():
    env_cmd=os.environ.get("AF3_RUN")
    if env_cmd and shutil.which(env_cmd): return shutil.which(env_cmd)
    p=os.environ.get("EBROOTALPHAFOLD3")
    if p:
        cand=os.path.join(p,"bin","run_alphafold.py")
        if os.path.isfile(cand) and os.access(cand, os.X_OK): return cand
    w=shutil.which("run_alphafold.py")
    if w: return w
    return None

def main():
    cmd=which_run()
    if not cmd:
        print("result: FAIL")
        print("reason: run_alphafold.py not found on PATH; set AF3_RUN or load the AlphaFold3 module")
        sys.exit(2)
    try:
        cp=subprocess.run([cmd,"--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
        out=cp.stdout or ""
        rc=cp.returncode
    except subprocess.TimeoutExpired:
        print("result: FAIL")
        print("cmd:", cmd)
        print("reason: timed out running '--help'")
        sys.exit(1)
    # Heuristics for success
    banner_ok=("AlphaFold 3 structure prediction script" in out) or ("usage:" in out and "run_alphafold.py" in out)
    ok=banner_ok and rc in (0,2,64)  # some CLIs exit 2/64 for help
    print("cmd:", cmd)
    print("exit_code:", rc)
    # print a short excerpt of help
    excerpt = "\n".join(out.splitlines()[:20])
    print("help_excerpt:\n" + textwrap.indent(excerpt, "  "))
    print("result:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__=="__main__":
    main()
