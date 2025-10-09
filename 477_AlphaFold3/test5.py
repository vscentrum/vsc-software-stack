import os, shutil, subprocess, sys

def run_with_flag(flag):
    exe = shutil.which("run_alphafold.py")
    if not exe:
        p=os.environ.get("EBROOTALPHAFOLD3")
        if p:
            cand=os.path.join(p,"bin","run_alphafold.py")
            if os.path.isfile(cand) and os.access(cand, os.X_OK): exe=cand
    if not exe:
        print(f"could not find run_alphafold.py; set EBROOTALPHAFOLD3 or PATH")
        return False, None, None
    cp = subprocess.run([exe, "--help", f"--flash_attention_implementation={flag}"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return cp.returncode in (0,1,2,64), cp.returncode, (cp.stdout or "")[:4000]

def main():
    ok1, rc1, out1 = run_with_flag("triton")
    ok2, rc2, out2 = run_with_flag("xla")
    print("flag_triton_ok:", ok1, "rc:", rc1)
    print("flag_xla_ok:", ok2, "rc:", rc2)
    # minimal heuristics: both should pass help parsing and show the banner
    banner = "AlphaFold 3 structure prediction script"
    ok = (ok1 and ok2 and (banner in (out1 or "")) and (banner in (out2 or "")))
    print("result:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
