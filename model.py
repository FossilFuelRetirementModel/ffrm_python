from pyomo.environ import *
import logging
logging.basicConfig(level=logging.INFO)
from pyomo.util.infeasible import log_infeasible_constraints
logging.basicConfig(level=logging.INFO) 
from pyomo.opt import SolverFactory
from pyomo.core.util import quicksum
from pathlib import Path
import pandas as pd
from energy_data_processor import load_excel_data, initialize_model_data
from result_processor import process_model_results, save_results_to_excel
import argparse
import time
import logging
import shutil
from datetime import datetime
from config import Config  # NEW: Import Config class for constants

def build_model(model_data, scenario, price_scenario):
    """
    Build a Pyomo optimization model based on the provided data and scenarios.

    Parameters:
    model_data (DataFrame): The data required to build the model.
    scenario (str): The scenario to be used in the model.
    price_scenario (str): The price scenario to be used in the model.

    Returns:
    ConcreteModel: A Pyomo ConcreteModel object.
    """
    # Input validation
    if model_data is None:
        raise ValueError("Model data cannot be None")
        
    required_attributes = ['plants', 'years', 'time_blocks', 'gen_data', 'price_gen']
    missing_attrs = [attr for attr in required_attributes if not hasattr(model_data, attr)]
    if missing_attrs:
        raise ValueError(f"Missing required model data attributes: {missing_attrs}")
    
    # Get valid scenarios from model_data instead of hardcoding
    valid_scenarios = list(model_data.scenarios.keys())
    valid_price_scenarios = ["MarketPrice", "AvgPPAPrice"]
    
    if scenario not in valid_scenarios:
        raise ValueError(f"Invalid scenario. Must be one of {valid_scenarios}")
    
    if price_scenario not in valid_price_scenarios:
        raise ValueError(f"Invalid price scenario. Must be one of {valid_price_scenarios}")
    # Create model
    try:
        model = ConcreteModel()

        # Sets
        model.g = Set(initialize=model_data.plants)
        model.y = RangeSet(min(model_data.years), min(max(model_data.years), Config.DEFAULT_END_YEAR))
        model.t = Set(initialize=model_data.time_blocks)
        # print("Sets:===========")
        # model.t.pprint()
        # time.sleep(15)
        # model.s = Set(initialize=model_data.scenarios.keys())
        # model.p = Set(initialize=model_data.price_scenarios.keys())
        model.s = Set(initialize=[scenario])
        model.p = Set(initialize=[price_scenario])
        
        # Parameters
        model.GenData = Param(model.g, initialize=model_data.gen_data.to_dict('index'))
        # Removed: Price_gen is no longer used, replaced by PriceGenTech
        # model.Price_gen = Param(model.y, initialize=model_data.price_gen.to_dict('index'))
        model.Price_Dist = Param(model.y, model.t, initialize=model_data.price_dist.stack().to_dict())
        model.Price_dur = Param(
            model.t, 
            initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] 
            # if t in model_data.price_dur.index else 0
            )
        # Technology-specific parameters
        model.TechParams = Param(
            model_data.tech_params.index.tolist(), 
            model_data.tech_params.columns.tolist(),
            initialize=lambda model, tech, param: model_data.tech_params.loc[tech, param] 
            if (tech in model_data.tech_params.index) and (param in model_data.tech_params.columns) else 0
            )
        
        model.FC_PPA = Param(
            model.g, model.y, 
            initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] 
            if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else Config.DEFAULT_FC_PPA_VALUE
            )#possible error here: 'HARDUAGANJ'
        
        # Helper to read GenData with fallback keys
        def row_get(g, keys, default=None):
            row = model.GenData[g]
            for k in keys:
                try:
                    if k in row:
                        return row[k]
                except Exception:
                    continue
            if default is not None:
                return default
            raise ValueError(f"None of the keys {keys} found for plant {g}")

        # Define price_Dist1 parameter, this parameter is used classify different price scenarios
        def price_dist1_init(model, y, p, t):
            """
            Initialize the price distribution parameter based on the price scenario.

            Returns: float: The price distribution value based on the scenario.
            """
            if p == "MarketPrice":
                return model.Price_Dist[y, t]  #  GAMS Price_Dist(y, t)
            elif p == "AvgPPAPrice":
                return 1  # NEW: Using 1 for AvgPPAPrice scenario (was hardcoded)
            else:
                raise NameError(f"Invalid price scenario: {p}")

        model.Price_Dist1 = Param(model.y, model.p, model.t, initialize=price_dist1_init)
        # model.Price_Dist1.pprint()
        
        # NEW: Technology set and plant mapping by technology
        model.tech = Set(initialize=model_data.technologies)
        model.plants_by_tech = Set(model.tech, initialize=lambda model, tech: [g for g in model.g if row_get(g, ["TECHNOLOGY", "Plant Type"]) == tech])
        
        # NEW: Per-technology generation targets (by year) for selected scenario
        # Build a dict mapping (year, tech) -> target value
        price_gen_by_tech_year = {}
        if hasattr(model_data, "price_gen") and not model_data.price_gen.empty:
            for idx in model_data.price_gen.index:
                idx_str = str(idx)
                # Handle different scenario naming patterns
                if idx_str.endswith(f"_{scenario}"):
                    # For BAU, AD_20, AD_40, etc.
                    tech_key = idx_str[:-len(f"_{scenario}")]
                elif scenario == "BAU" and idx_str.endswith("_BAU"):
                    # Fallback for BAU
                    tech_key = idx_str[:-4]
                else:
                    continue
                
                for y in model_data.years:
                    if y in model_data.price_gen.columns:
                        val = model_data.price_gen.at[idx, y]
                        if pd.notna(val):
                            price_gen_by_tech_year[(y, tech_key)] = float(val)
        model.PriceGenTech = Param(model.y, model.tech, initialize=price_gen_by_tech_year, default=0)
        
        # We now compute those derived Parameters
        def discount_rate_init(model, y):
            """Calculate the discount rate for a given year."""
            # Use a default technology for global discount rate (assuming all technologies have same rate)
            default_tech = list(model_data.tech_params.index)[0]  # Use first technology as default
            return 1 / (1 + model.TechParams[default_tech, "DiscountRate"]) ** (y - Config.BASE_YEAR)

        model.DR = Param(model.y, initialize=discount_rate_init, domain=NonNegativeReals)
        
        def initialize_life(model, g):
            """Calculate the life of the plant based on its start year."""
            start_year = row_get(g, ["STARTYEAR", "Start Year"])            
            if start_year > Config.BASE_YEAR:
                return 0  # For plants that haven't started yet
            return Config.BASE_YEAR - start_year

        model.life = Param(model.g, initialize=initialize_life, domain=NonNegativeIntegers)
        
        def initialize_cost(model, g, y):
            """Initialize the cost parameter based on the plant's age and technology."""
            # Get cost value, handling both 'COST' and 'VARIABLE COST' column names
            cost = row_get(g, ["COST", "VARIABLE COST", "Variable Cost ($/MWh)"])
            if cost is None:
                raise ValueError(f"Neither 'COST' nor 'VARIABLE COST' found for plant {g}")
            
            # Get the technology type for this plant
            tech_type = row_get(g, ["TECHNOLOGY", "Plant Type"])            
            
            if model.life[g] < Config.YOUNG_PLANT_THRESHOLD:
                return cost * (1 + model.TechParams[tech_type, "CostEsc_Lessthan10"]) ** (y - Config.BASE_YEAR)
            elif model.life[g] <= Config.OLD_PLANT_THRESHOLD:
                return cost * (1 + model.TechParams[tech_type, "CostEsc_10-30years"]) ** (y - Config.BASE_YEAR)
            else:
                return cost * (1 + model.TechParams[tech_type, "CostEsc_30plus"]) ** (y - Config.BASE_YEAR)

        model.cost = Param(model.g, model.y, initialize=initialize_cost, domain=NonNegativeReals)


        # Variables
        def calculate_generation_bounds(model, g, y, t):
            '''
            This function is used to set the bounds for the 'generation' variable, model.Gen
            '''
            # Get the technology type for this plant
            tech_type = row_get(g, ["TECHNOLOGY", "Plant Type"])            
            max_life = model.TechParams[tech_type, "MaxLife"]
            start_year = row_get(g, ["STARTYEAR", "Start Year"])            
            
            # If plant hasn't started yet or has exceeded max life, set generation to 0
            if y < start_year or (y + model.life[g] - Config.BASE_YEAR) > max_life:
                return (0, 0)
            else:
                return (0, row_get(g, ["CAPACITY", "Capacity (MW)"]))

        model.Gen = Var(model.g, model.y, model.t, domain=NonNegativeReals,bounds=calculate_generation_bounds)
        model.Cap = Var(model.g, model.y, domain=NonNegativeReals)
        model.Retire = Var(model.g, model.y, domain=Binary)
        model.TotNetRev = Var(domain=Reals)
            
        for g in model.g:
            for y in model.y:
                tech_type = row_get(g, ["TECHNOLOGY", "Plant Type"])                
                if y + model.life[g] - Config.BASE_YEAR > model.TechParams[tech_type, 'MaxLife']:
                    model.Cap[g, y].fix(Config.FIXED_CAPACITY_EXPIRED)
        # for g in model.g:
        #     if 2021 + model.life[g] - 2021 < model.Other["MaxLife", "Value"]:
        #         model.Retire[g, 2021].fix(0)     

        def rev_unit_init(model, g, y, price_scenario):
            '''
            Here we initialize the revenue unit of generation based on the price scenario
            '''
            if price_scenario == "MarketPrice":
                return row_get(g, ["MarketPrice", "Market Price ($/MWh)"])
            elif price_scenario == "AvgPPAPrice":
                return row_get(g, ["AvgPPAPrice", "AvgPPAPrice ($/MWh)"])
            else:
                raise NameError(f"Invalid price scenario: {price_scenario}")

        model.rev_unit = Param(
            model.g, model.y, model.p,
            initialize=rev_unit_init,
            within=NonNegativeReals
            )
        # print(model.GenData["UDUPI"])
        # print(model.rev_unit["UDUPI",2021,price_scenario])
        
        #####################################################################################
          ##### Constraints
        def max_coal_gen_rule(model, y):
            '''
            This function is used to set the maximum generation of coal plants
            '''
            
            
            # NEW: Using Config constants for time conversion (was hardcoded 8.76/1000)
            return quicksum(quicksum(
                model.Gen[g, y, t] * model.Price_dur[t] 
                for t in model.t
                    )for g in model.g )* Config.HOURS_PER_YEAR/Config.USD_TO_MILLIONS  == model.Price_gen[y][scenario]#sum(
                 #for s in model.s
        
        # Removed: global generation equality to undefined Price_gen totals
        # model.MaxCoalGen = Constraint(model.y, rule=max_coal_gen_rule)
        # print("OFFPEAK",model.Price_dur['Offpeak1'])
        # Minimum PLF
        def min_plf_rule(model, g, y):
            """
            This function is used to set the MINIMUM PLF rule
            """
            tech_type = row_get(g, ["TECHNOLOGY", "Plant Type"])            
            return sum(
            model.Gen[g, y, t] * model.Price_dur[t] #* Config.HOURS_PER_YEAR / Config.USD_TO_THOUSANDS
            for t in model.t
        ) >= model.Cap[g, y] * model.TechParams[tech_type, "MinPLF"]#* Config.HOURS_PER_YEAR / Config.USD_TO_THOUSANDS            
        model.MinPLF = Constraint(model.g, model.y, rule=min_plf_rule)
        # Maximum PLF
        def max_plf_rule(model, g, y):
            """
            This function is used to set the MAXIMUM PLF rule
            """
            tech_type = row_get(g, ["TECHNOLOGY", "Plant Type"])            
            return sum(
            model.Gen[g, y, t] * model.Price_dur[t] * Config.HOURS_PER_YEAR / Config.USD_TO_MILLIONS
            for t in model.t
        ) <= model.Cap[g, y] * model.TechParams[tech_type, "MaxPLF"]* Config.HOURS_PER_YEAR / Config.USD_TO_MILLIONS
            
        model.MaxPLF = Constraint(model.g, model.y, rule=max_plf_rule)
        
        # NEW: Per-technology generation goal constraints
        def tech_generation_goal_rule(model, y, tech):
            # Skip if this technology has no plants mapped
            if not any(True for _ in model.plants_by_tech[tech]):
                return Constraint.Skip
            return quicksum(
                quicksum(model.Gen[g, y, t] * model.Price_dur[t] for t in model.t)
                for g in model.plants_by_tech[tech]
            ) * Config.HOURS_PER_YEAR/Config.USD_TO_MILLIONS == model.PriceGenTech[y, tech]
        model.TechGenGoal = Constraint(model.y, model.tech, rule=tech_generation_goal_rule)
        
        # Capacity Balance
        def capacity_balance_rule(model, g, y):
            """
            This function is used to set the CAPACITY BALANCE rule
            """
            if y > Config.BASE_YEAR:
                return model.Cap[g, y] == model.Cap[g, y-1] - model.Retire[g, y] * row_get(g, ["CAPACITY"])
            else:
                return Constraint.Skip
        model.CapBal = Constraint(model.g, model.y, rule=capacity_balance_rule)
        
        def capacity_balance_rule1(model,g):
            cap0 = row_get(g, ["CAPACITY"])
            return model.Cap[g, Config.BASE_YEAR] == cap0 - model.Retire[g, Config.BASE_YEAR]* cap0
        
        model.CapBal1 = Constraint(model.g, rule=capacity_balance_rule1)

        
        # Retire Plants
        def max_retire_rule(model, g):
            """
            This function is used to set the MAXIMUM RETIRE rule
            """
            return sum(
                model.Retire[g, y] for y in model.y
            ) <= Config.MAX_RETIREMENTS_PER_PLANT
        model.MaxRetire = Constraint(model.g, rule=max_retire_rule)

        # Minimum Capacity per technology and year
        def min_capacity_tech_rule(model, y, tech):
            """
            Ensure capacity of plants in a technology meets that technology's generation target for the year.
            """
            # Skip if no target for this (y, tech)
            if (y, tech) not in model.PriceGenTech or model.PriceGenTech[y, tech] <= 0:
                return Constraint.Skip
            # Skip if no plants mapped to this technology
            if not any(True for _ in model.plants_by_tech[tech]):
                return Constraint.Skip
            required_capacity = (
                model.PriceGenTech[y, tech]
                * Config.TWH_TO_MWH
                / (Config.HOURS_PER_YEAR * Config.MAX_LOAD_FACTOR)
            )
            return sum(model.Cap[g, y] for g in model.plants_by_tech[tech]) >= required_capacity
        
        model.MinCapacityTech = Constraint(model.y, model.tech, rule=min_capacity_tech_rule)
        
        # Define objective function
        # print("DR:::::")
        # model.DR.pprint()
        # model.Price_dur.pprint()
        def objective_rule(model):
            """
            This function is used to set the OBJECTIVE function
            """
            total_objective = 0

            for y in model.y:
                year_contribution =  0

                # Calculate the first part of the objective function
                capacity = 0
                cost_per_mw= 0
                cost = 0 
                for g in model.g:
                    ad_scenarios = [s for s in model_data.scenarios.keys() if s != "BAU"]
                    if scenario in ad_scenarios:
                        capacity = model.Cap[g, y]
                    elif scenario == "BAU":
                        capacity = row_get(g, ["CAPACITY"])
                
                    if price_scenario == "AvgPPAPrice":
                        cost_per_mw = model.FC_PPA[g, y]/Config.USD_TO_THOUSANDS
                    elif price_scenario == "MarketPrice":
                        cost_per_mw = Config.DEFAULT_COST_PER_MW_MarketPrice
                    # cost+=cost_per_mw * capacity
                # year_contribution += -(capacity_sum * price_sum)  # to billion dollars
                    contract_price = row_get(g, ["ContractPriceMW"], 0.0)
                    cost += (cost_per_mw - contract_price) * capacity/1e6

                # Calculate the second part of the objective function
                revenue_sum = 0
                for g in model.g:
                    for t in model.t:
                        revenue_sum +=  (model.rev_unit[g, y, price_scenario] *model.Price_Dist1[y, price_scenario, t]- 
                                        model.cost[g, y])* model.Gen[g, y, t] * model.Price_dur[t]
                        # print(t, model.Gen[g, y, t].value, model.Price_dur[t],model.Price_Dist1[y, price_scenario, t])
                # year_contribution += # to billion dollars
                
                total_objective += model.DR[y]*(revenue_sum*Config.HOURS_PER_YEAR -cost)
            
            return total_objective/1e6
        model.Obj = Objective(rule=objective_rule,sense=maximize)

        return model
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise RuntimeError(f"Error creating optimization model: {str(e)}\nTraceback:\n{tb}")
def setup_argument_parser():
    """
    Set up and return the argument parser for command line options.
    
    Returns:
    ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Run Pyomo model with solver options.")
    parser.add_argument('--solver', type=str, default='gurobi', 
                       choices=['glpk', 'cplex', 'gurobi', 'cbc'],
                       help='Solver to use (e.g., glpk, cplex, gurobi, cbc).')
    parser.add_argument('--solver-options', type=str, nargs='*',
                       help='Solver options as key=value pairs.')
    parser.add_argument('--price-scenarios', type=str, nargs='+',
                       default=["AvgPPAPrice", "MarketPrice"],
                       choices=["MarketPrice", "AvgPPAPrice"],
                       help='Price scenarios to run.')
    parser.add_argument('--input-file', type=str,
                       default="250810 FFRM Data Input File - Philippines.xlsx",
                       help='Path to input Excel file.')
    parser.add_argument('--output-file', type=str,
                       default="Results.xlsx",
                       help='Path to output Excel file.')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: create timestamped directory)')
    return parser

def initialize_solver(args):
    """
    Initialize and configure the solver based on command line arguments.
    
    Parameters:
    args: Parsed command line arguments
    
    Returns:
    SolverFactory: Configured solver instance
    """
    # solvername='glpk'

    # solverpath_folder='C:/w64/glpk-4.65' #does not need to be directly on c drive

    # solverpath_exe='C:/w64/glpk-4.65/w64/glpsol' 
    
    solver = SolverFactory(args.solver)#,executable=solverpath_exe)
    if solver is None:
        raise RuntimeError(f"Solver {args.solver} not available")
    
    if args.solver_options:
        options = {k: v for opt in args.solver_options for k, v in [opt.split('=')]}
        for key, value in options.items():
            solver.options[key] = value
    
    return solver

def run_scenario(model_data, scenario, price_scenario, solver, output_dir=None):
    """
    Run a single scenario and return the results.
    
    Parameters:
    model_data: Initialized model data
    scenario (str): Scenario to run
    price_scenario (str): Price scenario to run
    solver: Configured solver instance
    
    Returns:
    dict: Results for the scenario
    """
    # from model_check import check_plf_constraints, verify_cost_calculations,check_capacity_constraints,validate_retirement_economics
    model = build_model(model_data, scenario, price_scenario)

    # Write the model to an LP file before solving
    lp_filename = f"{scenario}_{price_scenario}.lp"
    if output_dir:
        lp_filename = str(Path(output_dir) / lp_filename)
    model.write(lp_filename, io_options={'symbolic_solver_labels': True})

    result = solver.solve(model, tee=True)
    logging.getLogger('pyomo.core').setLevel(logging.INFO)
    log_infeasible_constraints(model, log_expression=True)    

    # FIXED: Removed problematic log_infeasible_constraints call with logger object
    # log = logging.getLogger('pyomo.core')
    # log.setLevel(logging.INFO)
    # log_infeasible_constraints(model, log)

    # if scenario == "AD":
    # debug_AD_scenario(model,scenario)
    # print("\nPost-solve checks:")    
    # check_capacity_constraints(model)
    # verify_cost_calculations(model)
    # check_plf_constraints(model)
    # validate_retirement_economics(model)
 
    # check_constraints(model)

    if (result.solver.status != SolverStatus.ok) or \
       (result.solver.termination_condition != TerminationCondition.optimal):
        print(f"\nModel is infeasible. LP file has been written to {lp_filename}")
        log_infeasible_constraints(model, log_expression=True)
        raise RuntimeError(f"Solver failed for scenario {scenario}_{price_scenario}")
    
    return process_model_results(model)

def check_constraints(model):
    """Check if key constraints are satisfied"""
    print("\nConstraint Verification:")
    
    # Check minimum PLF constraints
    for g in model.g:
        for y in model.y:
            plf = sum(
                model.Gen[g, y, t].value * model.Price_dur[t]
                for t in model.t
            ) / (model.Cap[g, y].value * 8760) if model.Cap[g, y].value > 0 else 0
            
            if model.Retire[g, y].value == 0 and plf<0.25:  #
                print(f"Plant {g} Year {y} PLF: {plf:.2f}")
    
    # Check capacity constraints
    for y in model.y:
        total_cap = sum(model.Cap[g, y].value for g in model.g)
        required_cap = sum(model.PriceGenTech[y, tech] * 1e6 / (8760 * 0.75) for tech in model.tech)
        if total_cap < required_cap:
            print(f"Year {y} Capacity Check:")
            print(f"  Total: {total_cap:.2f} MW")
            print(f"  Required: {required_cap:.2f} MW")

def main():
    """
    Main function to run the optimization model.
    """
    try:
        # Load and initialize data first to get available scenarios
        # Use default input file for initial loading
        default_input_file = "250810 FFRM Data Input File - Philippines.xlsx"
        file_path = Path(default_input_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        data = load_excel_data(file_path)
        model_data = initialize_model_data(data)
        
        # Set up argument parser with dynamic scenario choices
        parser = setup_argument_parser()
        available_scenarios = list(model_data.scenarios.keys())
        parser.add_argument('--scenarios', type=str, nargs='+', 
                           default=["AD_20","BAU"],
                           choices=available_scenarios,
                           help=f'Scenarios to run. Available: {", ".join(available_scenarios)}')
        
        # Parse arguments
        args = parser.parse_args()
        
        # Re-load data with the specified input file if different
        if args.input_file != default_input_file:
            file_path = Path(args.input_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Input file not found: {file_path}")
            
            data = load_excel_data(file_path)
            model_data = initialize_model_data(data)
        
        # NEW: Generate intermediate scenarios if any are requested
        # Check if any requested scenarios are intermediate scenarios (start with 'AD_')
        if any(scenario.startswith('AD_') for scenario in args.scenarios):
            print("Generating intermediate decarbonization scenarios...")
            from energy_data_processor import generate_intermediate_scenarios
            model_data = generate_intermediate_scenarios(model_data)
        
        # Setup output directory
        output_dir = None
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            # Create timestamped directory by default
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"results_{timestamp}")
        
        output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {output_dir.absolute()}")
        
        # Setup logging to output directory
        from energy_data_processor import setup_logging
        setup_logging(output_dir)
        
        # Update output file path to be in the output directory
        output_file = str(output_dir / Path(args.output_file).name)
        
        # Initialize solver
        solver = initialize_solver(args)
        
        # Run scenarios
        results = {}
        for scenario in args.scenarios:
            for price_scenario in args.price_scenarios:
                try:
                    key = f"{scenario}_{price_scenario}"
                    results[key] = run_scenario(model_data, scenario, 
                                             price_scenario, solver, output_dir)
                    print(f"Successfully completed scenario: {key}")
                except Exception as e:
                    print(f"Error in scenario {key}: {str(e)}")
                    continue
        
        # Save results
        try:
            save_results_to_excel(results, output_file, output_dir)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")
        
        print(f"\nAll results saved to: {output_dir}")
        for file_path in output_dir.glob("*"):
            print(f"  - {file_path.name}")
            
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return 1
    
    return 0

def debug_AD_scenario(model,s):
    """
    打印AD场景的关键变量进行对比
    """
    print(f"\n{s} Scenario Debug Info:")
    
    # 1. Check capacity values
    print("\nCapacity Values:")
    for g in model.g:
        for y in model.y:
            print(f"Plant {g}, Year {y}:")
            print(f"Cap: {model.Cap[g, y].value}")
            print(f"GenData Capacity: {model.GenData[g]['CAPACITY']}")
    
    # 2. Check revenue calculation
    print("\nRevenue Calculation:")
    for g in model.g:
        for y in model.y:
            for p in model.p:
                revenue = sum(
                    (
                        model.rev_unit[g, y, p] * 
                        model.Price_Dist1[y, p, t] - 
                        model.cost[g, y]
                    ) * model.Gen[g, y, t].value * 
                    model.Price_dur[t] * 8.76 / 1000
                    for t in model.t
                )
                print(f"Plant {g}, Year {y}, Price Scenario {p}:")
                print(f"Revenue: {revenue}")
    
    # 3. Check fixed cost
    print("\nFixed Cost Calculation:")
    for g in model.g:
        for y in model.y:
            fixed_cost = sum(
                (
                    model.Cap[g, y].value * 
                    (
                        model.FC_PPA[g, y] * (1-model.SetPriceScenario[p])/1e3 +
                        100 * model.SetPriceScenario[p]
                    )
                )
                for p in model.p
            ) / 1e6
            print(f"Plant {g}, Year {y}:")
            print(f"Fixed Cost: {fixed_cost}")

if __name__ == "__main__":
    main()