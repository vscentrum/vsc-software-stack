import os,sys,importlib.metadata as md
def v(p):
  try: return md.version(p)
  except: return None
print("python",sys.version.split()[0])
for p in ("rpy2","rpy2-rinterface","rpy2-robjects","tzlocal"):
  vv=v(p)
  if vv: print(p,vv)

import rpy2.robjects as ro
from rpy2.robjects.packages import importr

rver=ro.r("R.version.string")[0]
print("R",rver)

assert float(ro.r("1+1")[0])==2.0

v=ro.FloatVector([1.0,2.0,3.0])
assert float(ro.r("sum")(v)[0])==6.0

df=ro.DataFrame({"a":ro.IntVector([1,2,3]),"b":ro.StrVector(["x","y","z"])})
assert int(ro.r("nrow")(df)[0])==3
assert list(ro.r("names")(df))==["a","b"]

tmp=ro.r("tempfile()")[0]
ro.r("writeLines")(ro.StrVector(["hello"]), tmp)
assert ro.r("readLines")(tmp)[0]=="hello"

stats=importr("stats")
x=stats.rnorm(5)
assert len(x)==5

try:
  import numpy as np
  from rpy2.robjects import numpy2ri
  from rpy2.robjects.conversion import localconverter
  a=np.array([1.0,2.0,3.0])
  with localconverter(ro.default_converter + numpy2ri.converter):
    ra=ro.conversion.py2rpy(a)
    a2=ro.conversion.rpy2py(ra)
  assert float(a2.sum())==6.0
  print("numpy conversion OK")
except Exception as e:
  print("numpy conversion skipped:",type(e).__name__,e)

print("OK")
