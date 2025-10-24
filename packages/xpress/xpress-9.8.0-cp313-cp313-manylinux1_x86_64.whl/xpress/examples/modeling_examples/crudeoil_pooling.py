# Pooling example - nonlinear solving.
#
# This example models a problem of pooling crude oil from different sources
# to produce final products with specific properties considering flow and material
# balance constraints.
#
# (C) 1983-2025 Fair Isaac Corporation

import xpress as xp

p = xp.problem()

# Variables for crude oil sources.
crudeA = p.addVariable(name="A", lb=0.0)
crudeB = p.addVariable(name="B", lb=0.0)
crudeC = p.addVariable(name="C", lb=0.0)

# Flow variables.
crudeC_flowX = p.addVariable(name="CX", lb=0.0)
crudeC_flowY = p.addVariable(name="CY", lb=0.0)
pool_flowX   = p.addVariable(name="PX", lb=0.0)
pool_flowY   = p.addVariable(name="PY", lb=0.0)

# Variables for final products.
finalX = p.addVariable(name="X", lb=0.0, ub=100)
finalY = p.addVariable(name="Y", lb=0.0, ub=200)

# Pool quantity variable.
poolQ  = p.addVariable(name="poolQ", lb=0.0)

# Variables for cost and income.
cost    = p.addVariable(name="cost", lb=0.0)
income  = p.addVariable(name="income", lb=0.0)

# Cost and income constraints.
p.addConstraint(cost   == 6*crudeA + 16*crudeB + 10*crudeC,
                income == 9*finalX + 15*finalY)

# Flow balances:
#   Total amount of final products X and Y is the sum of the flow from the pool and the flow directly from crude C.
#   Total amount of crude C is distributed between the flows to final products X and Y.
#   Flow into the pool from crude A and crude B equals the flow out of the pool to final products X and Y.
p.addConstraint(finalX == pool_flowX + crudeC_flowX,
                finalY == pool_flowY + crudeC_flowY,
                crudeC == crudeC_flowX + crudeC_flowY,
                crudeA + crudeB == pool_flowX + pool_flowY)

# Material balances - ensure that the composition of the crude oils and the
# final products meet requirements regarding sulfur content.
pool_sulfur = 3*crudeA + crudeB == (pool_flowX + pool_flowY) * poolQ

p.addConstraint(pool_sulfur,
                pool_flowX * poolQ <= 0.5*crudeC_flowX + 2.5*crudeC_flowY,
                pool_flowY * poolQ <= 1.5*pool_flowY - 0.5*crudeC_flowY)

# Solve this problem with a local solver.
p.controls.nlpsolver = xp.constants.NLPSOLVER_LOCAL    # Solve with a local solver.
p.controls.localsolver = xp.constants.LOCALSOLVER_XSLP    # Choose SLP solver.

# Maximize the profit = difference between income and cost.
p.setObjective(income - cost,sense=xp.maximize)

p.optimize()

print('Solution: income is:', p.getSolution(income), 'and cost is:', p.getSolution(cost))
