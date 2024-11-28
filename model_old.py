from pyomo.environ import *
from pyomo.opt import SolverFactory
from pathlib import Path# # Model definition
from python_version import load_excel_data, initialize_model_data
# model = ConcreteModel()
from config import Config

# # Sets
# model.g = Set()  # Plant identifiers
# model.y = RangeSet(2021, 2040)  # Years from 2021 to 2040
# model.t = Set()  # Time blocks
# model.s = Set(initialize=['BAU', 'AD'])  # Scenarios
# model.p = Set(initialize=['MarketPrice', 'AvgPPAPrice'])  # Price scenarios

# # Parameters
# model.SetScenario = Param(model.s, initialize={'BAU': 1, 'AD': 0})
# model.SetPriceScenario = Param(model.p, initialize={'MarketPrice': 1, 'AvgPPAPrice': 0})



# model.GenData = Param(model.g, initialize={}, within=Any)
# model.Price_gen = Param(model.y, initialize={}, within=Any)
# model.Price_dist = Param(model.y, model.t, initialize={}, within=Any)
# model.Price_dur = Param(model.t, initialize={}, within=Any)
# model.Other = Param(initialize={}, within=Any)
# model.FC_PPA = Param(model.g, model.y, initialize={}, within=Any)

# Load data from Excel
file_path = Path("Input File (India-Coal Retirement).xlsx")  # Replace with your file path
print(file_path)

data = load_excel_data(file_path)
model_data = initialize_model_data(data)

# Build the Pyomo model
model = ConcreteModel()

# Sets
model.g = Set(initialize=model_data.plants)  # Plant identifiers
model.y = RangeSet(min(model_data.years), max(model_data.years))  # Years from 2021 to 2040
model.t = Set(initialize=model_data.time_blocks)  # Time blocks
model.s = Set(initialize=model_data.scenarios.keys())  # Scenarios
model.p = Set(initialize=model_data.price_scenarios.keys())  # Price scenarios

# Parameters
model.SetScenario = Param(model.s, initialize=model_data.scenarios)
model.SetPriceScenario = Param(model.p, initialize=model_data.price_scenarios)
print(model_data.price_dur)
model.GenData = Param(model.g, initialize=model_data.gen_data.to_dict('index'))
model.Price_gen = Param(model.y, initialize=model_data.price_gen.to_dict('index'))
model.Price_dist = Param(model.y, model.t, initialize=model_data.price_dist.stack().to_dict())
model.Price_dur = Param(model.t, initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] if t in model_data.price_dur.index else 0)
model.Other = Param(model_data.other.index.tolist(), model_data.other.columns.tolist(), 
        initialize=lambda model, k, v: model_data.other.loc[k, v] if (k in model_data.other.index) and (v in model_data.other.columns) else 0)
model.FC_PPA = Param(model.g, model.y, initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else 0)



# model.GenData.pprint()

# Derived Parameters
# model.Other.pprint()
model.DR = Param(model.y, initialize=lambda model, y: 1 / (1 + model.Other["DiscountRate","Value"]) ** (y - 2021))
model.life = Param(model.g, initialize=lambda model, g: 2021 - model.GenData[g]["STARTYEAR"])
model.cost = Param(model.g, model.y, initialize=lambda model, g, y: (
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_Lessthan10","Value"]) ** (y - 2021) if model.life[g] < 10 else
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_10-30years","Value"]) ** (y - 2021) if model.life[g] <= 30 else
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_30plus","Value"]) ** (y - 2021)
))

# Variables
model.Cap = Var(model.g, model.y, domain=NonNegativeReals)
model.Gen = Var(model.g, model.y, model.t, domain=NonNegativeReals)
model.Retire = Var(model.g, model.y, domain=Binary)
model.TotNetRev = Var(domain=Reals)
model.rev_unit = Var(model.g, model.y, model.p, domain=NonNegativeReals)  # Initialize rev_unit variable


def rev_unit_rule(model, g, y, p):
    if p == "MarketPrice":
        return model.rev_unit[g, y, p] == model.GenData[g]["MarketPrice"]
    elif p == "AvgPPAPrice":
        return model.rev_unit[g, y, p] == model.GenData[g]["FIXED COST"] + model.cost[g, y]
    else:
        return model.rev_unit[g, y, p] == 0  # Default case if needed

model.RevUnitConstraint = Constraint(model.g, model.y, model.p, rule=rev_unit_rule)


model.Price_gen.pprint()
# print(model.Price_gen[2021, 'BAU'])
# Constraints
def max_coal_gen_rule(model, y):
    return sum(model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000 for g in model.g for t in model.t) == sum(
        model.Price_gen[y][s] for s in model.s if model.SetScenario[s] == 1)
model.MaxCoalGen = Constraint(model.y, rule=max_coal_gen_rule)

def min_plf_rule(model, g, y):
    return sum(model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000 for t in model.t) >= model.Cap[g, y] * 8.76 / 1000 * model.Other["MinPLF","Value"]
model.MinPLF = Constraint(model.g, model.y, rule=min_plf_rule)

def max_plf_rule(model, g, y):
    return sum(model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000 for t in model.t) <= model.Cap[g, y] * 8.76 / 1000 * model.Other["MaxPLF","Value"]
model.MaxPLF = Constraint(model.g, model.y, rule=max_plf_rule)

def capacity_balance_rule(model, g, y):
    if y > 2021:
        return model.Cap[g, y] == model.Cap[g, y - 1] - model.Retire[g, y] * model.GenData[g]["CAPACITY"]
    else:
        return model.Cap[g, y] == model.GenData[g]["CAPACITY"] - model.Retire[g, y] * model.GenData[g]["CAPACITY"]
model.CapBal = Constraint(model.g, model.y, rule=capacity_balance_rule)

def retire_rule(model, g):
    return sum(model.Retire[g, y] for y in model.y) <= 1
model.MaxRetire = Constraint(model.g, rule=retire_rule)

def min_capacity_rule(model, y):
    return sum(model.Cap[g, y] for g in model.g) >= sum(
        model.Price_gen[y][s] for s in model.s if model.SetScenario[s] == 1) * 1e6 / (8760 * 0.75)
model.MinCapacity = Constraint(model.y, rule=min_capacity_rule)

# Objective
def objective_rule(model):
    return sum(
        model.DR[y] * (
            -sum(model.GenData[g]["CAPACITY"] * (model.FC_PPA[g, y] * model.SetPriceScenario[p] + 100 * (1 - model.SetPriceScenario[p]))
                 for g in model.g for p in model.p) / 1e6 +
            sum((model.Gen[g, y, t] * model.Price_dist[y, t] * model.Price_dur[t] * 8.76 / 1000) -
                model.cost[g, y] for g in model.g for t in model.t)
        ) for y in model.y
    )
model.Obj = Objective(rule=objective_rule, sense=maximize)

# Solve the model
solver = SolverFactory('cplex')  # Replace 'glpk' with your solver
# solver.options['mipgap'] = 0.06  # 设置为 6% 的相对间隙

result = solver.solve(model, tee=True)

# Display results
model.display()

# 假设模型求解成功
if result.solver.termination_condition == TerminationCondition.optimal:
    # 从 Pyomo 模型中提取结果
    # Parameters to calculate
    totgen = {}
    NetRev = {}
    Retire_BAU = {}
    Capacity_BAU = {}
    Summary = {}
    PlantGen = {}
    # Calculate total generation per year
    for y in model.y:
        totgen[y] = sum(
            model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
            for g in model.g for t in model.t
        )

    # Calculate net revenue per plant per year
    for g in model.g:
        for y in model.y:
            fixed_costs = sum(
                model.GenData[g]['CAPACITY'] *
                (model.FC_PPA[g, y] * model.SetPriceScenario[p] +
                100 * (1 - model.SetPriceScenario[p]))
                for p in model.p
            ) / 1e6
            variable_revenue = sum(
                model.rev_unit[g, y, p].value *
                sum(
                    model.Gen[g, y, t].value *
                    model.Price_dist[y, t] *
                    model.Price_dur[t] *
                    8.76 / 1000
                    for t in model.t
                )
                for p in model.p if model.SetPriceScenario[p] == 1
            )
            NetRev[g, y] = -fixed_costs + variable_revenue

    # Calculate retirements under BAU scenario
    for g in model.g:
        for y in model.y:
            Retire_BAU[g, y] = model.Retire[g, y].value

    # Calculate capacity under BAU scenario
    for g in model.g:
        for y in model.y:
            Capacity_BAU[g, y] = model.Cap[g, y].value

    # Generate summary outputs per year
    for y in model.y:
        total_capacity = sum(model.Cap[g, y].value for g in model.g)
        total_retirements = sum(model.Retire[g, y].value for g in model.g)
        total_net_rev = sum(NetRev[g, y] for g in model.g)
        Summary[y] = {
            'TotalCapacity': total_capacity,
            'TotalRetirements': total_retirements,
            'TotalNetRevenue': total_net_rev
        }

    # Calculate plant-level generation per year
    for g in model.g:
        PlantGen[g] = {
            y: sum(
                model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
                for t in model.t
            )
            for y in model.y
        }


    # Display or save results
    print("Total Generation per Year (totgen):", totgen)
    print("Net Revenue per Plant per Year (NetRev):", NetRev)
    print("Retirements under BAU Scenario (Retire_BAU):", Retire_BAU)
    print("Capacity under BAU Scenario (Capacity_BAU):", Capacity_BAU)
    print("Summary per Year (Summary):", Summary)
    print("Plant Generation per Year (PlantGen):", PlantGen)
    import pandas as pd
    retirement_schedule = {}

    for g in model.g:
        retirement_years = []
        for y in model.y:
            if model.Retire[g, y].value == 1:  # Check if the plant is set to retire in this year
                retirement_years.append(1)  # Indicate retirement
            else:
                retirement_years.append(0)  # Indicate no retirement
        retirement_schedule[g] = retirement_years

    # Create a DataFrame for the retirement schedule
    retirement_df = pd.DataFrame.from_dict(retirement_schedule, orient='index', columns=[str(year) for year in model.y])
    retirement_df.index.name = 'Plant'

    # Save the retirement schedule to a CSV file
    retirement_df.to_csv('RetirementSchedule.csv')
    # Save Summary
    summary_df = pd.DataFrame.from_dict(Summary, orient='index')
    summary_df.to_csv('Summary.csv')

    # Save Net Revenue
    net_rev_df = pd.DataFrame.from_dict(NetRev, orient='index')
    net_rev_df.to_csv('NetRevenue.csv')

    # Save Plant Generation
    plant_gen_df = pd.DataFrame.from_dict(PlantGen, orient='index')
    plant_gen_df.to_csv('PlantGeneration.csv')
