import importlib.metadata as md

print("cuda-core:", md.version("cuda-core"))
print("cuda-python:", md.version("cuda-python"))

import cuda.core
import cuda.core.experimental as cexp
from cuda.core.experimental import Program, ProgramOptions

print("cuda.core:", cuda.core.__file__)
print("cuda.core.experimental:", cexp.__file__)
print("Program:", Program)
print("ProgramOptions:", ProgramOptions)
print("OK")