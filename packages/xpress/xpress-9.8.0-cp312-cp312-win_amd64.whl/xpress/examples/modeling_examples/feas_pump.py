# Feasibility pump - algorithm implementation using the Xpress Python interface.
#
# (C) 1983-2025 Fair Isaac Corporation

import xpress as xp

def getRoundedSol(sol, I):
    rsol = sol[:]
    for i in I:
        rsol[i] = round(sol[i])
    return rsol

def computeViol(p, viol, rtype, m):
    for i in range(m):
        if rtype[i] == 'L':
            viol[i] = -viol[i]
        elif rtype[i] == 'E':
            viol[i] = abs(viol[i])
    return max(viol[:m])

p = xp.problem()
p.readProb('Data/test.lp')

n = p.attributes.cols  # Number of columns.
m = p.attributes.rows  # Number of rows.
N = range(n)

vtype = p.getColType(0, n-1)  # Obtain variable type ('C', for continuous).

I = [i for i in N if vtype[i] != 'C']  # Discrete variables.

V = p.getVariable()

p.lpOptimize()
sol = p.getSolution()
roundsol = getRoundedSol(sol, I)
slack = p.calcSlacks(roundsol)
rtype = p.getRowType(0, m - 1)

# If x_I is the vector of integer variables and x_I* is its LP value,
# the auxiliary problem is:
#
# min |x_I - x_I*|_1
# s.t. x in X
#
# where X is the original feasible set. Add new variables y and set
# their sum as the objective, then define the l1 norm with the
# constraints:
#
# y_i >= x_i - x_i*
# y_i >= - (x_i - x_i*)

y = [p.addVariable() for i in I]

p.setObjective(xp.Sum(y))  # Objective.

# RHS to be configured later.
defPenaltyPos = [y[i] >= V[I[i]] for i in range(len(I))]
defPenaltyNeg = [y[i] >= - V[I[i]] for i in range(len(I))]

p.addConstraint(defPenaltyPos, defPenaltyNeg)

slackTol = 1e-4

while computeViol(p, slack, rtype, m) > slackTol:

    # Modify definition of penalty variable.
    p.chgRHS(defPenaltyPos, [-roundsol[i] for i in I])
    p.chgRHS(defPenaltyNeg, [roundsol[i] for i in I])

    # Reoptimize.
    p.lpOptimize()
    sol = p.getSolution()

    roundsol = getRoundedSol(sol, I)
    slack = p.calcSlacks(roundsol)

# Found feasible solution.
print('Feasible solution:', roundsol[:n])
