import pandas as pd
import numpy as np
from pyomo.environ import ConcreteModel, Var, Objective, Constraint, SolverFactory, NonNegativeReals

# Load Excel Data
excel_file_path = "Input File (India-Coal Retirement).xlsx"
xls = pd.ExcelFile(excel_file_path)

# Load relevant sheets into dataframes
coal_plant_data = pd.read_excel(xls, sheet_name='CoalPlantData', skiprows=2)
fc_ppa_data = pd.read_excel(xls, sheet_name='FC_PPA', skiprows=3)
price_gen_data = pd.read_excel(xls, sheet_name='Price_Gen', skiprows=3)
price_distribution_data = pd.read_excel(xls, sheet_name='Price_Distribution', skiprows=2)
other_data = pd.read_excel(xls, sheet_name='Other', skiprows=1)

# Cleaning and structuring the data
coal_plant_data.columns = ['Plant', 'VariableCost', 'FixedCost', 'AvgPPAPrice', 'MarketPrice', 'Capacity', 'StartYear']
coal_plant_data = coal_plant_data.dropna().reset_index(drop=True)

other_data.columns = ['Parameter', 'Value', 'Description']
other_data = other_data.set_index('Parameter')

# Extracting parameters
discount_rate = other_data.at['DiscountRate', 'Value']
cost_esc_lessthan10 = other_data.at['CostEsc_Lessthan10', 'Value']
cost_esc_10_30 = other_data.at['CostEsc_10-30Years', 'Value'] if 'CostEsc_10-30Years' in other_data.index else 0.02  # Assumed default
cost_esc_30plus = other_data.at['CostEsc_30Plus', 'Value'] if 'CostEsc_30Plus' in other_data.index else 0.03  # Assumed default

# Creating a discount rate function for different years
def calculate_discount_rate(years, rate):
    return 1 / (1 + rate) ** (np.array(years) - 1)

# Calculating discount rates for the years 2021 to 2040
years = np.arange(2021, 2041)
discount_factors = calculate_discount_rate(years - 2020, discount_rate)

# Calculating plant life and cost based on escalation rates
coal_plant_data['Life'] = 2021 - coal_plant_data['StartYear']

costs = []
for _, row in coal_plant_data.iterrows():
    plant_cost = []
    for year in years:
        life = row['Life']
        if life < 10:
            cost = row['VariableCost'] * (1 + cost_esc_lessthan10) ** (year - 2021)
        elif 10 <= life <= 30:
            cost = row['VariableCost'] * (1 + cost_esc_10_30) ** (year - 2021)
        else:
            cost = row['VariableCost'] * (1 + cost_esc_30plus) ** (year - 2021)
        plant_cost.append(cost)
    costs.append(plant_cost)

# Adding cost data to the dataframe
cost_df = pd.DataFrame(costs, columns=years, index=coal_plant_data['Plant'])

# Optimization using Pyomo
model = ConcreteModel()

# Defining decision variables (0 <= usage <= 1)
model.usage = Var(coal_plant_data['Plant'], domain=NonNegativeReals, bounds=(0, 1))

# Objective function: minimize total variable cost
def objective_rule(m):
    return sum(m.usage[plant] * coal_plant_data.loc[coal_plant_data['Plant'] == plant, 'VariableCost'].values[0] for plant in coal_plant_data['Plant'])
model.objective = Objective(rule=objective_rule, sense=1)  # Minimize cost

# Constraint: ensure the total capacity meets a minimum threshold
def capacity_constraint_rule(m):
    return sum(m.usage[plant] * coal_plant_data.loc[coal_plant_data['Plant'] == plant, 'Capacity'].values[0] for plant in coal_plant_data['Plant']) >= 10000  # Example minimum capacity requirement
model.capacity_constraint = Constraint(rule=capacity_constraint_rule)

# Solving the model
solver = SolverFactory('glpk')
solver.solve(model)

# Extracting the optimized values
coal_plant_data['OptimalUsage'] = [model.usage[plant].value for plant in coal_plant_data['Plant']]

# Display the updated dataframe with optimal usage
# Instead of using ace_tools, use standard display methods
print(coal_plant_data)

# Alternatively, save to a CSV file for analysis
coal_plant_data.to_csv("Optimal_Plant_Usage_and_Costs.csv", index=False)