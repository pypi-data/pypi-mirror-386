# Fire station location example using SciPy sparse arrays for efficiency.
#
# The fire station location problem attemps to minimize the number of fire stations
# to build amongst a set of towns, with each town being a candidate for
# hosting a fire station. Each town must be served by a fire station built
# on a town with a travel time no longer than a defined threshold (e.g. 15 minutes).
# In this example, we solve the location problem using a SciPy sparse
# matrix with the xpress.Dot() operator for efficiency.
#
# (C) 1983-2025 Fair Isaac Corporation

import xpress as xp
import numpy as np
import scipy

num_towns = 6     # Number of towns.

t_time = np.array([[ 0, 15, 25, 35, 35, 25],     # Travel times between towns.
                   [15,  0, 30, 40, 25, 15],
                   [25, 30,  0, 20, 30, 25],
                   [35, 40, 20,  0, 20, 30],
                   [35, 25, 35, 20,  0, 19],
                   [25, 15, 25, 30, 19,  0]])

avail = (t_time <= 15).astype(int)                # NumPy array of binary values equal to 1 if t_time <= 15.

avail_sparse = scipy.sparse.csr_array(avail)      # Convert to SciPy sparse matrix format.

# Print travel times in both formats for comparison.
print("NumPy format: ", avail, sep="\n")
print("SciPy format: ", avail_sparse, sep="\n")

p = xp.problem()      # Create Xpress problem.

x = p.addVariables(num_towns, vartype=xp.binary)  # Create NumPy array of variables.

# Serve all towns, amongst those eligible to be selected for each.
p.addConstraint(xp.Dot(avail_sparse,x) >= 1)      # Creates set of constraints with RHS = 1.

p.setObjective(xp.Sum(x))                         # Minimize number of towns selected for a fire station.

p.optimize()

# Print solution.
print("Number of stations: ", round(p.attributes.objval))
xsol = p.getSolution(x)
print("Located at towns",[s+1 for s in range(num_towns) if xsol[s] >= 0.99])
