# A facility location problem, demonstrating how to use Pandas with the
# Xpress Python interface.
#
# The problem is to choose which facilities to open in order to satisfy
# customer demand. The constraints are:
# - each customer must be served from exactly one facility
# - customers can only be served from open facilities
# - customer demand must be satisfied
# - facility capacity must not be exceeded
# We minimize the sum of transport cost (between customer and facility) and
# the cost for opening a facility.
#
# (C) 2025 Fair Isaac Corporation

import pandas as pd
import xpress as xp

# Customer ids, names and demand are stored in a data frame
customers = pd.DataFrame({
    'customer_id': ['C1', 'C2', 'C3', 'C4'],
    'name': ['Customer 1', 'Customer 2', 'Customer 3', 'Customer 4'],
    'demand': [80, 270, 250, 130]
}).set_index('customer_id')

# Facility ids, names, capacities and opening costs are stored in a data frame
facilities = pd.DataFrame({
    'facility_id': ['F1', 'F2', 'F3'],
    'name': ['Facility 1', 'Facility 2', 'Facility 3'],
    'capacity': [500, 400, 600],
    'cost': [1000, 900, 1000]
}).set_index('facility_id')

# Define distances between each customer and each facility in a matrix
distances = pd.DataFrame(
    [
        # Customer:
        # 1, 2, 3, 4
        [4, 6, 9, 2],   # Facility 1
        [5, 4, 7, 8],   # Facility 2
        [6, 3, 4, 4]    # Facility 3
    ],
    index=facilities.index,
    columns=customers.index
)

# Convert the matrix to a flat data frame, columns will be:
# facility_id, customer_id, distance
routes = distances.stack().reset_index(name='distance')

# Create the Xpress problem
p = xp.problem()

# Binary variables: whether to open each facility
facilities['open'] = p.addVariables(len(facilities), name='open', vartype=xp.binary)

# Continuous variables: how many units to serve from each facility to each customer
serve_vars = p.addVariables(len(facilities), len(customers), name='serve')
routes['serve'] = pd.Series(serve_vars.reshape(len(routes)), dtype='xpressobj')

# Demand must be met for each customer
p.addConstraint(routes.groupby('customer_id').serve.sum() == customers.demand)

# Units served from each facility must not exceed capacity, and only open facilities may serve units
p.addConstraint(routes.groupby('facility_id').serve.sum() <= facilities.capacity * facilities.open)

# Minimize total facility cost
p.setObjective(facilities.cost.dot(facilities.open))

# Solve the problem
p.optimize()
print()

# Check the result
if p.attributes.solstatus != xp.SolStatus.OPTIMAL:
    print(f'Problem was not solved to optimality. Status: {p.attributes.solstatus.name}')
else:
    # Fetch the solution values
    facilities['open_sol'] = p.getSolution(facilities.open)
    routes['serve_sol'] = p.getSolution(routes.serve)

    # Print the solution
    print('Facilities to open:')
    open_facilities = facilities[facilities.open_sol > 0.5]
    print(open_facilities.to_string(columns=['name'], header=False, index=False))

    print()
    for c in customers.itertuples():
        print(f'{c.name} served by:')
        served_by = routes[(routes.customer_id == c.Index) & (routes.serve_sol > 0)]
        # Join the facilities table to get the facility names
        print(served_by.join(facilities, on='facility_id').to_string(columns=['name', 'serve_sol'], header=False, index=False))
