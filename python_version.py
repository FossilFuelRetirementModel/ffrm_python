import pandas as pd
from pathlib import Path
from config import Config
from typing import Dict, List
from dataclasses import dataclass
from pyomo.environ import *
@dataclass
class ModelData:
    """Class to hold all model data structures"""
    # Basic sets
    years: List[int]              # y: Years from 2021 to 2040
    plants: List[str]             # g: Plant identifiers (from coal_plant_data)
    time_blocks: List[str]        # t: Time blocks (from price_distribution)
    scenarios: Dict[str, int]     # s: BAU and AD scenarios
    price_scenarios: Dict[str, int]  # p: Market Price and PPA Price scenarios
    
    # Parameter data
    gen_data: pd.DataFrame        # GenData(g,*)  Plant-level data
    price_gen: pd.DataFrame       # Price_gen(y,*) Forecasted average price and total coal generation per year
    price_dist: pd.DataFrame      # Price_dist(y,t) Distribution of prices as multiple of average price
    price_dur: pd.DataFrame       # Price_dur(t,*) Duration of price blocks
    other: pd.DataFrame          # Other(*,*) Other parameters
    fc_ppa: pd.DataFrame         # FC_PPA(g,y) Mandatory capacity payment at 85% PLF for 25 years

def initialize_model_data(data: dict) -> ModelData:
    """
    Initialize model data structures from loaded Excel data
    
    Args:
        data: Dictionary containing DataFrames from Excel
    
    Returns:
        ModelData object containing all model structures
    """
    return ModelData(
        years=Config.YEARS,
        plants=data['coal_plant_data'].index.tolist(),  # Assuming plant ID is index
        time_blocks=data['price_distribution'].columns.tolist(),   # Assuming time blocks are column names
        scenarios=Config.SCENARIOS,
        price_scenarios=Config.PRICE_SCENARIOS,
        
        # Data tables
        gen_data=data['coal_plant_data'],
        price_gen=data['price_gen'],
        price_dist=data['price_distribution'],
        price_dur=data['price_dur'],
        other=data['other'],
        fc_ppa=data['fc_ppa']
    )

def load_excel_data(file_path: Path) -> dict:
    """Load all required data from Excel file"""
    try:
        # Read coal plant data
        coal_plant_data = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['COAL_PLANT'],
            **Config.EXCEL_CONFIG['CoalPlantData']
        )

        # Read price distribution data (includes time blocks and price duration)
        price_distribution = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['price_dist']
        )

        # Read time blocks (column headers from price distribution)
        time_blocks = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['time_blocks']
        )
        print("==============================================")
        print(Config.EXCEL_CONFIG['Price_Distribution']['price_dur'])
        # Read price duration
        price_duration = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['price_dur']
        )

        # Read price generation data
        price_gen = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_GEN'],
            **Config.EXCEL_CONFIG['Price_Gen']
        )

        # Read other data
        other = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['OTHER'],
            **Config.EXCEL_CONFIG['Other']
        )

        # Read FC PPA data
        fc_ppa = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['FC_PPA'],
            **Config.EXCEL_CONFIG['FC_PPA']
        )

        return {
            'coal_plant_data': coal_plant_data,
            'price_distribution': price_distribution,
            'time_blocks': time_blocks,
            'price_dur': price_duration,
            'price_gen': price_gen,
            'other': other,
            'fc_ppa': fc_ppa
        }

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise
    
def build_model(model_data: ModelData):
    model = ConcreteModel()

    # Sets
    model.years = Set(initialize=model_data.years)
    model.plants = Set(initialize=model_data.plants)
    model.time_blocks = Set(initialize=model_data.time_blocks)
    model.scenarios = Set(initialize=model_data.scenarios.keys())
    model.price_scenarios = Set(initialize=model_data.price_scenarios.values())
    
    # Variables
    model.Cap = Var(model.plants, model.years, within=NonNegativeReals)
    model.Gen = Var(model.plants, model.years, model.time_blocks, within=NonNegativeReals)
    model.Retire = Var(model.plants, model.years, within=Binary)
    model.TotNetRev = Var(within=NonNegativeReals)
    model.rev_unit = Var(model.plants, model.years, model.price_scenarios, within=NonNegativeReals)

    # Parameters
    # print(model_data.fc_ppa.loc["RATNAGIRI","2021"])
    model.fc_ppa = Param(model.plants, model.years, initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else 0)
    
    
    model.price_dist = Param(model_data.years, model.time_blocks, initialize=lambda model, y, t: model_data.price_dist.loc[y, t] if (y in model_data.price_dist.index) and (t in model_data.price_dist.columns) else 0)
    
    model.price_gen = Param(model_data.years, initialize=lambda model, y: model_data.price_gen.loc[y].to_dict()) 
    # Assuming price_gen is indexed by years
    print(model.time_blocks)
    print("====================")
    print(model_data.price_dur.loc[model_data.price_dur.index[0],"PercentTime"])
    print("====================")
   
    # print(model_data.price_dist)
    # print(model_data.time_blocks)
    model.price_dur = Param(model.time_blocks, initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] if t in model_data.price_dur.index else 0)  # Assuming price_dur is indexed by time blocks

    model.other = Param(model_data.other.index.tolist(), model_data.other.columns.tolist(), 
        initialize=lambda model, k, v: model_data.other.loc[k, v] if (k in model_data.other.index) and (v in model_data.other.columns) else 0)

    # Initialize GenData as a parameter
    model.gen_data = Param(model.plants, model_data.years, initialize=lambda model, g, y: model_data.gen_data.loc[g, str(y)] if g in model_data.gen_data.index and str(y) in model_data.gen_data.columns else 0)

  
   
    # print(model_data.gen_data)
    DR = {y: 1 / (1 + model_data.other.loc["DiscountRate", "Value"]) ** (y - 2021) for y in model_data.years}
    life = {g: 2021 - model_data.gen_data.loc[g, "STARTYEAR"] for g in model_data.plants}

    # Cost calculation based on plant age
    def cost_rule(model, g, y):
        if life[g] < 10:
            return model_data.gen_data.loc[g, "AvgPPAPrice"] * (1 + model_data.other.loc["CostEsc_Lessthan10", "Value"]) ** (y - 2021)
        elif 10 <= life[g] <= 30:
            return model_data.gen_data.loc[g, "AvgPPAPrice"] * (1 + model_data.other.loc["CostEsc_10-30years", "Value"]) ** (y - 2021)
        else:
            return model_data.gen_data.loc[g, "AvgPPAPrice"] * (1 + model_data.other.loc["CostEsc_30plus", "Value"]) ** (y - 2021)

    model.Cost = Param(model.plants, model.years, initialize=cost_rule)
    # print("----------------------")
    # model.Gen.pprint()
    # print("----------------------")

    # Objective Function
    def objective_rule(model):
        return sum(
        DR[y] * (
            - sum(
                model_data.gen_data.loc[g, "CAPACITY"] * (
                    model.fc_ppa[g, y] * (1 if p == "MarketPrice" else 0) + 100 * (1 - (1 if p == "MarketPrice" else 0))
                )
                for p in model.price_scenarios  # Iterate over the set directly
            ) / 1e6 +
            sum(
                (model.rev_unit[g, y, p] * model.price_dist[y, t] - model.Cost[g, y]) * model.Gen[g, y, t] * model.price_dur[t] * 8.76 / 1000
                for t in model_data.time_blocks
            )
        )
        for g in model.plants for y in model.years for p in model.price_scenarios  # Include p in the outer loop
    )

    model.objective = Objective(rule=objective_rule, sense=maximize)
    
    # Constraints
    # model.price_gen.pprint()
    def max_coal_gen_rule(model, y):
        return sum(model.Gen[g, y, t] * model.price_dur[t] * 8.76 / 1000 for g in model.plants for t in model.time_blocks) == sum(model.price_gen[y][s] for s in model.scenarios)  # Access price_gen directly
    model.MaxCoalGen = Constraint(model.years, rule=max_coal_gen_rule)

    # Minimum Plant Load Factor Constraint , "PercentTime"
    model.price_dur.pprint()
    def min_plf_rule(model, g, y):
        return sum(model.Gen[g, y, t] * model.price_dur[t] * 8.76 / 1000 for t in model.time_blocks) >= model.Cap[g, y] * 8.76 / 1000 * model_data.other.loc["MinPLF", "Value"]

    model.MinPLF = Constraint(model.plants, model.years, rule=min_plf_rule)

    # Maximum Plant Load Factor Constraint
    def max_plf_rule(model, g, y):
        return sum(model.Gen[g, y, t] * model.price_dur[t] * 8.76 / 1000 for t in model.time_blocks) <= model.Cap[g, y] * 8.76 / 1000 * model_data.other.loc["MinPLF", "Value"]

    model.MaxPLF = Constraint(model.plants, model.years, rule=max_plf_rule)

    # Retirement Limit Constraint
    def max_retire_rule(model, g):
        return sum(model.Retire[g, y] for y in model.years) <= 1

    model.MaxRetire = Constraint(model.plants, rule=max_retire_rule)

    # Capacity Balance Constraint
    def capacity_balance_rule(model, g, y):
        years_list = list(model.years)  # Convert the set to a list
        if y > years_list[0]:  # Check if the current year is greater than the first year
            previous_year = years_list[years_list.index(y) - 1]  # Get the previous year
            return model.Cap[g, y] == model.Cap[g, previous_year] - model.Retire[g, y] * model_data.gen_data.loc[g, "CAPACITY"]
        else:
            return model.Cap[g, y] == model_data.gen_data.loc[g, "CAPACITY"] - model.Retire[g, y] * model_data.gen_data.loc[g, "CAPACITY"]

    model.CapBal = Constraint(model.plants, model.years, rule=capacity_balance_rule)

    # Minimum Capacity Constraint
    def min_capacity_rule(model, y):
        return sum(model.Cap[g, y] for g in model.plants) >= sum(model.price_gen[y][s] for s in model.scenarios) * 1000000 / (8760 * 0.75)

    model.MinCapacity = Constraint(model.years, rule=min_capacity_rule)

    return model

if __name__ == "__main__":
    try:
        # Load Excel data
        raw_data = load_excel_data(Config.EXCEL_PATH)
        
        # Initialize model data structures
        model_data = initialize_model_data(raw_data)
        # print(model_data.price_dur)
        # Build the optimization model
        model = build_model(model_data)
        
        # Solve the model
        solver = SolverFactory('ipopt')  # You can change 'glpk' to your preferred solver
        results = solver.solve(model, tee=True)  # tee=True will print solver output
        # Check the solver status
        if results.solver.termination_condition == TerminationCondition.optimal:
            print("Optimal solution found.")
        else:
            print("Solver did not find an optimal solution.")
        
        # Print key data for verification
        print("\n=== Model Data Overview ===")
        print(f"\nYears: {model_data.years}")
        print(f"Number of years: {len(model_data.years)}")
        
        print(f"\nPlants: {model_data.plants}")
        print(f"Number of plants: {len(model_data.plants)}")
        
        print(f"\nTime blocks: {model_data.time_blocks}")
        print(f"Number of time blocks: {len(model_data.time_blocks)}")
        
        print("\nScenarios:")
        for scenario, value in model_data.scenarios.items():
            print(f"- {scenario}: {'Active' if value == 1 else 'Inactive'}")
        
        print("\nPrice Scenarios:")
        for scenario, value in model_data.price_scenarios.items():
            print(f"- {scenario}: {'Active' if value == 1 else 'Inactive'}")
        
        print("\nGeneration Data Preview:")
        print(model_data.gen_data.head())
        print(f"Gen Data Shape: {model_data.gen_data.shape}")
        
        print("\nPrice Generation Data Preview:")
        print(model_data.price_gen.head())
        print(f"Price Gen Shape: {model_data.price_gen.shape}")
        
        print("\nPrice Distribution Preview:")
        print(model_data.price_dist.head())
        print(f"Price Distribution Shape: {model_data.price_dist.shape}")
        
        print("\nPrice Duration Preview:")
        print(model_data.price_dur.head())
        print(f"Price Duration Shape: {model_data.price_dur.shape}")
        
        print("\nFC PPA Data Preview:")
        print(model_data.fc_ppa.head())
        print(f"FC PPA Shape: {model_data.fc_ppa.shape}")
        
        print("\nOther Data Preview:")
        print(model_data.other.head())
        print(f"Other Data Shape: {model_data.other.shape}")
        
        # Check for any missing values
        print("\n=== Missing Values Check ===")
        for attr_name, df in {
            'gen_data': model_data.gen_data,
            'price_gen': model_data.price_gen,
            'price_dist': model_data.price_dist,
            'price_dur': model_data.price_dur,
            'fc_ppa': model_data.fc_ppa,
            'other': model_data.other
        }.items():
            missing = df.isnull().sum().sum()
            print(f"{attr_name}: {missing} missing values")
        # Display results
        print("\n=== Results ===")
        for g in model.plants:
            for y in model.years:
                retired = model.Retire[g, y].value
                if retired == 1:  # Check if the plant is retired in this year
                    print(f"Plant: {g}, Year: {y}, Capacity: {model.Cap[g, y].value}, Generation: {model.Gen[g, y, t].value for t in model.time_blocks}, Retired: {retired} (Retirement Year)")
                # else:
                #     print(f"Plant: {g}, Year: {y}, Capacity: {model.Cap[g, y].value}, Generation: {model.Gen[g, y, t].value for t in model.time_blocks}, Retired: {retired}")
                    
    except Exception as e:
        print(f"Error in data initialization: {str(e)}")
        raise