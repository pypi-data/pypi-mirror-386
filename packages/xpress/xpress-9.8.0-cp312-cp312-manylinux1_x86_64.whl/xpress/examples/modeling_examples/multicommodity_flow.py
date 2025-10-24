# Multicommodity flow example.
#
# (C) 1983-2025 Fair Isaac Corporation

import xpress as xp
import numpy as np
import math

np.random.seed(100)

# Random network generation.
n = 10          # Number of nodes
thres = 0.4     # Density of network
thresdem = 0.8  # Density of demand mesh

# Generate random forward stars for each node.

fwstars = {}

for i in range(n):
    fwstar = []
    for j in range(n):
        if j != i:
            if np.random.random() < thres:
                fwstar.append(j)
    fwstars[i] = fwstar

# Backward stars are generated based on the forward stars.

bwstars = {i: [] for i in range(n)}

for j in fwstars.keys():
    for i in fwstars[j]:
        bwstars[i].append(j)

# Create arc array.

arcs = []
for i in range(n):
    for j in fwstars[i]:
        arcs.append((i, j))

# Create random demand between node pairs.

dem = []

for i in range(n):
    for j in range(n):
        if i != j and np.random.random() < thresdem:
            dem.append((i, j, math.ceil(200*np.random.random())))

# U is the unit capacity of each edge.
U = 1000
# Edge cost.
c = {(i, j): math.ceil(10 * np.random.random()) for (i, j) in arcs}

p = xp.problem()

# Flow variables.
f = {(i, j, d): p.addVariable(name='f_{0}_{1}_{2}_{3}'.format(i, j, dem[d][0],
                                                       dem[d][1]))
     for (i, j) in arcs for d in range(len(dem))}

# Capacity variables.
x = {(i, j): p.addVariable(vartype=xp.integer, name='cap_{0}_{1}'.format(i, j))
     for (i, j) in arcs}

def demand(i, d):
    if dem[d][0] == i:  # Source
        return 1
    elif dem[d][1] == i:  # Destination
        return -1
    else:
        return 0


# Flow conservation constraints: total flow balance at node i for each demand d
# must be 0 if i is an intermediate node, 1 if i is the source of demand d, and
# -1 if i is the destination.

flow = {(i, d):
        xp.constraint(constraint=xp.Sum(f[i, j, d]
                                        for j in range(n) if (i, j) in arcs) -
                      xp.Sum(f[j, i, d] for j in range(n) if (j, i) in arcs)
                      == demand(i, d),
                      name='cons_{0}_{1}_{2}'.format(i, dem[d][0], dem[d][1]))
        for d in range(len(dem)) for i in range(n)}

# Capacity constraints: weighted sum of flow variables must be contained in the
# total capacity installed on the arc (i, j).
capacity = {(i, j):
            xp.constraint(constraint=xp.Sum(dem[d][2] * f[i, j, d]
                                            for d in range(len(dem)))
                          <= U * x[i, j],
                          name='capacity_{0}_{1}'.format(i, j))
            for (i, j) in arcs}

p.addConstraint(flow, capacity)

p.setObjective(xp.Sum(c[i, j] * x[i, j] for (i, j) in arcs))

# Compact declaration:
#
# p = xp.problem(f, x, flow, capacity,
#                xp.Sum(c[i, j] * x[i, j] for (i, j) in arcs))

p.optimize()
