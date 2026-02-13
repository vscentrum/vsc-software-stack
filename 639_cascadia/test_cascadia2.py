import argparse, sys, os, platform, subprocess, traceback, importlib, pkgutil, inspect

def v(x): return getattr(x, "__version__", "unknown")
def eprint(*a): print(*a, file=sys.stderr)

def run(cmd):
  p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
  return p.returncode, p.stdout

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", help="Path to a .ckpt to test Lightning load_from_checkpoint")
  ap.add_argument("--strict", action="store_true", help="Require strict checkpoint loading (default: non-strict fallback allowed)")
  ap.add_argument("--no-walk", action="store_true", help="Only import cascadia + cascadia.cascadia (skip importing all submodules)")
  ap.add_argument("--cli-help", action="store_true", help="Also run: cascadia --help and cascadia sequence --help")
  args = ap.parse_args()

  print("== Platform ==")
  print("python:", sys.version.replace("\n"," "))
  print("exe:", sys.executable)
  print("os:", platform.platform())

  try:
    import torch
    print("\n== Torch ==")
    print("torch:", v(torch))
    print("torch cuda build:", getattr(torch.version, "cuda", None))
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
      print("gpu:", torch.cuda.get_device_name(0))
      x = torch.randn(256, 256, device="cuda")
      y = (x @ x).float().mean().item()
      print("cuda matmul ok:", y)
  except Exception as ex:
    eprint("FAIL: torch import/compute failed:", repr(ex))
    return 2

  lm_bases = []
  try:
    import lightning
    from lightning.pytorch import LightningModule as LM2
    lm_bases.append(LM2)
    print("\n== Lightning ==")
    print("lightning:", v(lightning))
  except Exception as ex:
    print("\n== Lightning ==")
    print("lightning: not importable:", repr(ex))
  try:
    import pytorch_lightning as pl
    from pytorch_lightning import LightningModule as LM1
    lm_bases.append(LM1)
    print("pytorch_lightning:", v(pl))
  except Exception as ex:
    print("pytorch_lightning: not importable:", repr(ex))

  try:
    import cascadia
    print("\n== Cascadia ==")
    print("cascadia:", v(cascadia))
    print("cascadia file:", getattr(cascadia, "__file__", None))
  except Exception as ex:
    eprint("FAIL: cascadia import failed:", repr(ex))
    return 3

  cli_mod = None
  for m in ["cascadia.cascadia", "cascadia.cli", "cascadia.__main__"]:
    try:
      cli_mod = importlib.import_module(m)
      print("cli module:", m)
      break
    except Exception:
      pass
  if not cli_mod:
    print("cli module: not found via imports (this is OK if only console_script is installed)")

  bad_imports = []
  imported = []
  if args.no_walk:
    imported = [cascadia] + ([cli_mod] if cli_mod else [])
  else:
    for m in pkgutil.walk_packages(cascadia.__path__, cascadia.__name__ + "."):
      name = m.name
      try:
        imported.append(importlib.import_module(name))
      except Exception as ex:
        bad_imports.append((name, ex))

  if bad_imports:
    print("\n== Import problems (possible API/runtime breaks) ==")
    for name, ex in bad_imports[:30]:
      print(" -", name, "=>", repr(ex))
    if len(bad_imports) > 30:
      print(" ... ({} more)".format(len(bad_imports) - 30))

  candidates = []
  if lm_bases:
    for mod in imported:
      try:
        for _, obj in inspect.getmembers(mod, inspect.isclass):
          if obj.__module__ != mod.__name__: 
            continue
          for base in lm_bases:
            try:
              if obj is base: 
                continue
              if issubclass(obj, base):
                candidates.append(obj)
                break
            except Exception:
              pass
      except Exception:
        pass

  print("\n== LightningModule candidates in cascadia ==")
  if candidates:
    for c in sorted({candidates[i] for i in range(len(candidates))}, key=lambda x: x.__module__+"."+x.__name__):
      print(" -", c.__module__ + "." + c.__name__)
  else:
    print(" (none found by introspection)")

  ckpt_ok = None
  if args.ckpt:
    print("\n== Checkpoint load ==")
    if not os.path.exists(args.ckpt):
      eprint("FAIL: ckpt not found:", args.ckpt)
      return 4
    try:
      import torch
      blob = torch.load(args.ckpt, map_location="cpu")
      k = list(blob.keys()) if hasattr(blob, "keys") else type(blob)
      print("torch.load ok; keys/type:", k if isinstance(k, list) else k)
    except Exception as ex:
      eprint("FAIL: torch.load failed (serialization issue):", repr(ex))
      return 5

    tried = []
    for cls in candidates:
      if not hasattr(cls, "load_from_checkpoint"):
        continue
      try:
        tried.append(cls.__module__ + "." + cls.__name__)
        m = cls.load_from_checkpoint(args.ckpt, map_location="cpu", strict=True)
        print("load_from_checkpoint strict OK with:", tried[-1])
        ckpt_ok = True
        break
      except Exception as ex:
        if args.strict:
          print("strict FAIL with:", tried[-1], "=>", repr(ex))
        else:
          try:
            m = cls.load_from_checkpoint(args.ckpt, map_location="cpu", strict=False)
            print("load_from_checkpoint non-strict OK with:", tried[-1])
            ckpt_ok = True
            break
          except Exception as ex2:
            print("FAIL with:", tried[-1], "=>", repr(ex2))

    if ckpt_ok is not True:
      print("No LightningModule could load this checkpoint via load_from_checkpoint().")
      print("Tried:", tried[:20], ("... (+%d more)" % (len(tried)-20) if len(tried)>20 else ""))

  if args.cli_help:
    print("\n== CLI help smoke test ==")
    rc, out = run(["cascadia", "--help"])
    print("cascadia --help rc:", rc)
    print(out[:2000])
    rc, out = run(["cascadia", "sequence", "--help"])
    print("cascadia sequence --help rc:", rc)
    print(out[:2000])

  ok = True
  if bad_imports:
    ok = False
  if args.ckpt and ckpt_ok is not True:
    ok = False

  print("\n== RESULT ==")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 10

if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except SystemExit:
    raise
  except Exception:
    traceback.print_exc()
    raise SystemExit(99)
