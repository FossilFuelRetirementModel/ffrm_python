from pyomo.environ import *
import pyomo.environ as pyo

model = ConcreteModel("version 1")
model.x = Var([1,2,3], domain=NonNegativeReals)
model.OBJ = Objective(expr = 1*model.x[1] + 2*model.x[2]+model.x[3]) #, rule=Objective_rule)

model.Constraint1 = Constraint(expr = -1*model.x[1] -2*model.x[2] <= -4.5)
model.Constraint2 = Constraint(expr = -2*model.x[1] -3*model.x[3] <= -8)  # changed to "2"
model.Constraint3 = Constraint(expr =1*model.x[2] +1*model.x[3] ==10)     # changed to "3"
opt = SolverFactory('glpk')
opt.solve(model)

model.display()

print('\n\n+++++++++++++++++++++++++++++++\n')
### alternatively with "rule"

model = ConcreteModel("version 2")
model.x = Var([1,2,3], domain=NonNegativeReals)

### OBJECTIVE
def objective_rule(model):
    return 1*model.x[1] + 2*model.x[2]+model.x[3]
model.OBJ = Objective(rule=objective_rule)

### CONSTRAINTS
model.Constraint1 = Constraint(expr = -1*model.x[1] -2*model.x[2] <= -4.5)
model.Constraint2 = Constraint(expr = -2*model.x[1] -3*model.x[3] <= -8)  # changed to "2"
model.Constraint3 = Constraint(expr =1*model.x[2] +1*model.x[3] ==10)     # changed to "3"
opt = SolverFactory('glpk')
results = opt.solve(model)

model.display()
print('Solver Status:', results.solver.status)
print('Termination Condition:', results.solver.termination_condition)
# Get and display the optimal values for x1, x2, and the maximum profit
# x1_opt = pyo.value(model.x)
profit_opt = pyo.value(model.OBJ)
# print(f'Optimal production of P1 (x1): {x1_opt}')
print(f'Maximum Profit: ${profit_opt}')