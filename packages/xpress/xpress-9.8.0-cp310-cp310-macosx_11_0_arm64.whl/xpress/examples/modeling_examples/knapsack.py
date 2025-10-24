# Example of a knapsack problem formulated with the Xpress Python interface.
#
# (C) 1983-2025 Fair Isaac Corporation

import xpress as xp
import numpy as np

S = range(5)                                # The set {0,1,2,3,4}
value = np.array([102, 512, 218, 332, 41])
weight = np.array([21, 98, 44, 59, 9])

p = xp.problem("knapsack")

x = p.addVariables(5, vartype=xp.binary)
profit = xp.Dot(value,x)

p.addConstraint(xp.Dot(weight,x) <= 130)
p.setObjective(profit, sense=xp.maximize)

p.optimize()
