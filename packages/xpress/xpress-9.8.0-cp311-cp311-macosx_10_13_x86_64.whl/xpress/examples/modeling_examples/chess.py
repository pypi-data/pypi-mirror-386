# Example for the use of the Python language (Small LP-problem).
#
# Changing column types.
#
# (C) 2018-2025 Fair Isaac Corporation

import xpress as xp

p = xp.problem()

small = p.addVariable()
large = p.addVariable()

# Now we have the constraints.

p.addConstraint(3*small + 2*large <= 400)  # Limit on available machine time.
p.addConstraint(small + 3*large <= 200)    # Limit on available wood.

# Define the objective function.
p.setObjective(5*small + 20*large, sense=xp.maximize)

p.optimize()

print('')
print("Here are the LP results")
print("Objective value is ", p.attributes.objval)
print("Make ", p.getSolution(small), " small sets, and ",
      p.getSolution(large), " large sets")

p.chgColType([small, large], ['I', 'I'])

p.optimize()

print('')
print("Here are the IP results")
print("Objective value is ", p.attributes.objval)
print("Make ", p.getSolution(small), " small sets, and ",
      p.getSolution(large), " large sets")
