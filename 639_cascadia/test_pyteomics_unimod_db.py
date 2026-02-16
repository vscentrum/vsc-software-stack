import os, sys, pathlib, socket
from urllib.parse import urlparse, unquote

def die(msg, code=1):
  print("ERROR:", msg); raise SystemExit(code)

def sqlite_url_to_path(s):
  u = urlparse(s)
  if u.scheme != "sqlite": die(f"not a sqlite URL: {s}")
  p = unquote(u.path)
  if not p: die("sqlite URL has empty path")
  p = os.path.normpath(p)
  if not p.startswith("/"): p = "/" + p
  return p

def block_network():
  try:
    import urllib.request as ur
    def _blocked(*a, **k): raise RuntimeError("NETWORK BLOCKED: urllib attempted")
    ur.urlretrieve = _blocked
    ur.urlopen = _blocked
  except Exception:
    pass
  try:
    import requests
    def _blocked_req(*a, **k): raise RuntimeError("NETWORK BLOCKED: requests attempted")
    requests.get = _blocked_req
    requests.request = _blocked_req
  except Exception:
    pass
  def _blocked_conn(*a, **k): raise RuntimeError("NETWORK BLOCKED: socket attempted")
  socket.create_connection = _blocked_conn

def main():
  print("python:", sys.version.split()[0])
  try:
    import pyteomics
    from pyteomics.mass import unimod
  except Exception as e:
    die(f"import failed: {e}")

  print("pyteomics:", getattr(pyteomics, "__version__", "unknown"))

  db = os.environ.get("PYTEOMICS_UNIMOD_DB")
  if not db: die("PYTEOMICS_UNIMOD_DB is not set")
  print("PYTEOMICS_UNIMOD_DB:", db)

  db_path = pathlib.Path(sqlite_url_to_path(db))
  print("db_path:", str(db_path))

  if not db_path.is_file(): die("unimod.db does not exist at db_path")
  if db_path.stat().st_size < 1024: die("unimod.db looks too small; likely not created correctly")

  block_network()

  try:
    u = unimod.Unimod()

    eng = getattr(u, "engine", None)
    if eng is not None:
      print("engine.url:", str(eng.url))

    Mod = getattr(unimod, "Modification", None)
    if Mod is None: die("cannot access unimod.Modification (unexpected pyteomics layout)")

    n = u.session.query(Mod).count()
    print("Modification rows:", n)
    if n <= 0: die("Modification table is empty; DB may be corrupt")

    ox = u.by_title("Oxidation")
    if ox is None:
      print("Oxidation: not found (DB still OK)")
    else:
      info = {}
      for k in ("record_id", "id", "title", "full_name", "name"):
        if hasattr(ox, k):
          info[k] = getattr(ox, k)
      print("Oxidation:", info if info else f"(found {type(ox).__name__})")

  except Exception as e:
    die(f"Unimod() failed (or tried network): {e}")

  print("PASS: unimod.db exists and Unimod() loads from it with network blocked.")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
