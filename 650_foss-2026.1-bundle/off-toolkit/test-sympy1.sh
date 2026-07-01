#!/usr/bin/env bash
set -euo pipefail

python -s <<'PY'
import warnings

warnings.simplefilter("error", DeprecationWarning)

import mpmath
import sympy
from mpmath.libmp import mpf_ln
from sympy import E, Float, Rational, Symbol, cos, integrate, log, pi, simplify, sin, sqrt
from sympy.geometry import Point, Polygon

print("SymPy:", sympy.__version__)
print("mpmath:", mpmath.__version__)

assert sympy.__version__ == "1.14.0"
assert hasattr(mpmath.libmp, "mpf_ln")
assert mpf_ln((0, 2, 0, 2), 53) == mpmath.libmp.mpf_ln((0, 2, 0, 2), 53)

# Exercises SymPy evalf/log path that previously imported deprecated mpf_log.
assert abs(float(log(Float(2)).evalf(50)) - mpmath.log(2)) < 1e-15
assert simplify(log(E) - 1) == 0

# Exercises evalf multiplication path that previously called deprecated mpmath.libmp.bitcount.
assert sqrt(Rational(2)).evalf(80).is_Float
assert (pi * sqrt(2)).evalf(80).is_Float

# Regression-style checks matching the mpmath 1.4.x failures seen in the test suite.
square1 = Polygon(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1))
square2 = Polygon(Point(2, 0), Point(3, 0), Point(3, 1), Point(2, 1))
assert square1._do_poly_distance(square2) == 1

x, y = Symbol("x"), Symbol("y")
p = x**2 + y*sin(y) + cos(y)
Qy = integrate(p, (y, 0, pi))
assert Qy.has(pi)

# Basic complex/numerical mpmath-backed evaluation.
z = (log(1 + sympy.I) + sqrt(2)).evalf(50)
assert z.is_number

print("SymPy/mpmath compatibility smoke test passed")
PY