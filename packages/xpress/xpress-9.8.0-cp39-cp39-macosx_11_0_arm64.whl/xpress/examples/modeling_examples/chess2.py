# Example for the use of the Python language (Small LP-problem).
#
# Retrieve constraint activity values.
#
# (C) 2018-2025 Fair Isaac Corporation

import xpress as xp

DescrV = {}
DescrC = {}

p = xp.problem()

xs = p.addVariable()
xl = p.addVariable()

mc_time = 3*xs + 2*xl <= 400  # Limit on available machine time.
wood = xs + 3*xl <= 200       # Limit on available wood.

# Define the variable and constraint descriptions. Since the arrays
# and the indexing sets are dynamic they grow with each new variable
# description added:
DescrV = {xs: " Number of small chess sets",
          xl: " Number of large chess sets"}

DescrC = {mc_time: " Limit on available machine time",
          wood: " Limit on available wood"}

p.addConstraint(mc_time, wood)

# Define the objective function.
p.setObjective(5*xs + 20*xl, sense=xp.maximize)

p.optimize()

# Print out the solution.
print("Solution:\n Objective: ", p.attributes.objval)
print(DescrV[xs], ":", p.getSolution(xs), ",",
      DescrV[xl], ":", p.getSolution(xl))

print(" Constraint activity:")
print(DescrC[mc_time], ": ", mc_time.rhs - mc_time.getSlack(), "\n",
      DescrC[wood],    ": ", wood.rhs - wood.getSlack(), sep='')
