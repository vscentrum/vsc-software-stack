import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

c = -np.array([0., 1.])
A = np.array([[-1, 1], [3, 2], [2, 3]])
b_u = np.array([1., 12., 12.])
b_l = np.array([-np.inf, -np.inf, -np.inf])

constraints = LinearConstraint(A, b_l, b_u)
integrality = np.ones(2, dtype=int)
bounds = Bounds([0, 0], [np.inf, np.inf])

res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)
print(res.status, res.message, res.x, res.fun)