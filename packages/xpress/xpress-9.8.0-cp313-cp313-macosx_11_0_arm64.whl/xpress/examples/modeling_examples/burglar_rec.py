# Example for the use of the Python language (Burglar problem).
#
# Reading data from file.
#
# (C) 2018-2025 Fair Isaac Corporation

import xpress as xp
from Data.burglar_rec_dat import I

WTMAX = 102  # Maximum weight allowed.
ITEMS = set(["camera", "necklace", "vase", "picture", "tv", "video",
             "chest", "brick"])  # Index set for items.

p = xp.problem()

take = {i: p.addVariable(vartype=xp.binary) for i in I.keys()}

# Objective: maximize total value.
p.setObjective(xp.Sum(I[i][0] * take[i] for i in ITEMS),
               sense=xp.maximize)

# Weight restriction.
p.addConstraint(xp.Sum(I[i][1] * take[i] for i in ITEMS) <= WTMAX)

p.optimize()  # Solve the MIP-problem.

# Print out the solution.
print("Solution:\n Objective: ", p.attributes.objval)
takesol = p.getSolution(take)
for i in ITEMS:
    print(" take(", i, "): ", takesol[i])
