# Solving a min-cost-flow problem using the Xpress Python interface.
#
# (C) 1983-2025 Fair Isaac Corporation

import numpy as np  # for matrix and vector products
import xpress as xp

# Digraph definition

V = [1, 2, 3, 4, 5]                                   # Vertices.
E = [[1, 2], [1, 4], [2, 3], [3, 4], [4, 5], [5, 1]]  # Arcs.

n = len(V)  # Number of nodes.
m = len(E)  # Number of arcs.

# Generate incidence matrix: begin with a NxM zero matrix.
A = np.zeros((n,m))

# Then for each column i of the matrix, add a -1 in correspondence to
# the tail of the arc and a 1 for the head of the arc.  Because Python
# uses 0-indexing, the row of A should be the node index minus one.
for i, edge in enumerate(E):
    A[edge[0] - 1][i] = -1
    A[edge[1] - 1][i] =  1

print("incidence matrix:\n", A)

# One (random) demand for each node.
demand = np.random.randint(100, size=n)
# Balance demand at nodes.
demand[0] = - sum(demand[1:])

cost = np.random.randint(20, size=m)  # Integer, random arc costs.

p = xp.problem('network flow')

# Flow variables declared on arcs
flow = p.addVariables(m)

p.addConstraint(xp.Dot(A, flow) == -demand)
p.setObjective(xp.Dot(cost, flow))

p.optimize()

print(cost, demand)

sol = p.getSolution(flow)

for i in range(m):
    print('flow on', E[i], ':', sol[i])
