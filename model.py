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
    
    valid_scenarios = ["BAU", "AD"]
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
        model.y = RangeSet(min(model_data.years), max(model_data.years))
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
        model.Price_gen = Param(model.y, initialize=model_data.price_gen.to_dict('index'))
        model.Price_Dist = Param(model.y, model.t, initialize=model_data.price_dist.stack().to_dict())
        model.Price_dur = Param(
            model.t, 
            initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] 
            # if t in model_data.price_dur.index else 0
            )
        model.Other = Param(
            model_data.other.index.tolist(), 
            model_data.other.columns.tolist(),
            initialize=lambda model, k, v: model_data.other.loc[k, v] 
            # if (k in model_data.other.index) and (v in model_data.other.columns) else 0
            )
        
        model.FC_PPA = Param(
            model.g, model.y, 
            initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] 
            if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else 100
            )#possible error here: 'HARDUAGANJ'
        

        # Define price_Dist1 parameter, this parameter is used classify different price scenarios
        def price_dist1_init(model, y, p, t):
            """
            Initialize the price distribution parameter based on the price scenario.

            Returns: float: The price distribution value based on the scenario.
            """
            if p == "MarketPrice":
                return model.Price_Dist[y, t]  #  GAMS Price_Dist(y, t)
            elif p == "AvgPPAPrice":
                return 1#model.Price_Dist[y, t]#1  
            else:
                raise NameError(f"Invalid price scenario: {p}")

        model.Price_Dist1 = Param(model.y, model.p, model.t, initialize=price_dist1_init)
        # model.Price_Dist1.pprint()
        
        # We now compute those derived Parameters
        def discount_rate_init(model, y):
            """Calculate the discount rate for a given year."""
            return 1 / (1 + model.Other["DiscountRate", "Value"]) ** (y - 2021)

        model.DR = Param(model.y, initialize=discount_rate_init, domain=NonNegativeReals)
        
        def initialize_life(model, g):
            """Calculate the life of the plant based on its start year."""
            start_year = model.GenData[g]["STARTYEAR"]
            if start_year > 2021:
                return 0  # For plants that haven't started yet
            return 2021 - start_year

        model.life = Param(model.g, initialize=initialize_life, domain=NonNegativeIntegers)
        
        def initialize_cost(model, g, y):
            """Initialize the cost parameter based on the plant's age."""
            # Get cost value, handling both 'COST' and 'VARIABLE COST' column names
            cost = model.GenData[g].get("COST") or model.GenData[g].get("VARIABLE COST")
            if cost is None:
                raise ValueError(f"Neither 'COST' nor 'VARIABLE COST' found for plant {g}")
            
            if model.life[g] < 10:
                return cost * (1 + model.Other["CostEsc_Lessthan10", "Value"]) ** (y - 2021)
            elif model.life[g] <= 30:
                return cost * (1 + model.Other["CostEsc_10-30years", "Value"]) ** (y - 2021)
            else:
                return cost * (1 + model.Other["CostEsc_30plus", "Value"]) ** (y - 2021)

        model.cost = Param(model.g, model.y, initialize=initialize_cost, domain=NonNegativeReals)


        # Variables
        def calculate_generation_bounds(model, g, y, t):
            '''
            This function is used to set the bounds for the 'generation' variable, model.Gen
            '''
            max_life = model.Other["MaxLife", "Value"]
            start_year = model.GenData[g]["STARTYEAR"]
            
            # If plant hasn't started yet or has exceeded max life, set generation to 0
            if y < start_year or (y + model.life[g] - 2021) > max_life:
                return (0, 0)
            else:
                return (0, model.GenData[g]["CAPACITY"])

        model.Gen = Var(model.g, model.y, model.t, domain=NonNegativeReals,bounds=calculate_generation_bounds)
        model.Cap = Var(model.g, model.y, domain=NonNegativeReals)
        model.Retire = Var(model.g, model.y, domain=Binary)
        model.TotNetRev = Var(domain=Reals)
            
        for g in model.g:
            for y in model.y:
                if y + model.life[g] - 2021 > model.Other['MaxLife', 'Value']:
                    model.Cap[g, y].fix(0.0)
        # for g in model.g:
        #     if 2021 + model.life[g] - 2021 < model.Other["MaxLife", "Value"]:
        #         model.Retire[g, 2021].fix(0)     

        def rev_unit_init(model, g, y, price_scenario):
            '''
            Here we initialize the revenue unit of generation based on the price scenario
            '''
            if price_scenario == "MarketPrice":
                return model.GenData[g]["MarketPrice"]
            elif price_scenario == "AvgPPAPrice":
                return model.GenData[g]["FIXED COST"] + model.cost[g,y]
                ############################################################
                # IS "FIXED COST" Correct? Should it be "AvgPPAPrice"?
                ############################################################
            else:
                raise NameError(f"Invalid price scenario: {price_scenario}")

        # model.rev_unit = Constraint(model.g, model.y, model.p, rule=rev_unit_rule)
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
            
            
            # ((g,t), Gen(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000) =e= Sum(s$SetScenario(s), Price_Gen(y,s)) ;
            return quicksum(quicksum(
                model.Gen[g, y, t] * model.Price_dur[t] 
                for t in model.t
                    )for g in model.g )* 8.76/1000  == model.Price_gen[y][scenario]#sum(
                 #for s in model.s
        
        model.MaxCoalGen = Constraint(model.y, rule=max_coal_gen_rule)
        # print("OFFPEAK",model.Price_dur['Offpeak1'])
        # Minimum PLF
        def min_plf_rule(model, g, y):
            """
            This function is used to set the MINIMUM PLF rule
            """
            return sum(
                model.Gen[g, y, t] * model.Price_dur[t] #* 8.76 / 1000
                for t in model.t
            ) >= model.Cap[g, y] *model.Other["MinPLF", "Value"]#* 8.76 / 1000            
        model.MinPLF = Constraint(model.g, model.y, rule=min_plf_rule)
        # Maximum PLF
        def max_plf_rule(model, g, y):
            """
            This function is used to set the MAXIMUM PLF rule
            """
            return sum(
                model.Gen[g, y, t] * model.Price_dur[t] #* 8.76 / 1000
                for t in model.t
            ) <= model.Cap[g, y] * model.Other["MaxPLF", "Value"]#* 8.76 / 1000
            
        model.MaxPLF = Constraint(model.g, model.y, rule=max_plf_rule)
        
        # Capacity Balance
        def capacity_balance_rule(model, g, y):
            """
            This function is used to set the CAPACITY BALANCE rule
            """
            if y>2021:
                return model.Cap[g, y] == model.Cap[g, y-1] - model.Retire[g, y] * model.GenData[g]["CAPACITY"]
            else:
                return Constraint.Skip
        model.CapBal = Constraint(model.g, model.y, rule=capacity_balance_rule)
        
        def capacity_balance_rule1(model,g):
            return model.Cap[g, 2021] == model.GenData[g]["CAPACITY"]- model.Retire[g, 2021]* model.GenData[g]["CAPACITY"]
        
        model.CapBal1 = Constraint(model.g, rule=capacity_balance_rule1)

        
        # Retire Plants
        def max_retire_rule(model, g):
            """
            This function is used to set the MAXIMUM RETIRE rule
            """
            return sum(
                model.Retire[g, y] for y in model.y
            ) <= 1
        model.MaxRetire = Constraint(model.g, rule=max_retire_rule)

        # Minimum Capacity
        def min_capacity_rule(model, y):
            """
            This function is used to set the MINIMUM CAPACITY rule
            """
            #unit of Capacity is MW, unit of Price_gen is TWh
            return sum(
                model.Cap[g, y] for g in model.g
            ) >= model.Price_gen[y][scenario] *1000000 / (8760 * 0.75)
          
        model.MinCapacity = Constraint(model.y, rule=min_capacity_rule)
        
        def min_capacity_rule1(model, y):
            """
            This function is used to set the MINIMUM CAPACITY rule
            """
            #unit of Capacity is MW, unit of Price_gen is TWh
            return sum(
                model.Cap[g, y] for g in model.g
            ) <= model.Price_gen[y][scenario] *1000000 / (8760 * 0.74)
          
        model.MinCapacity1 = Constraint(model.y, rule=min_capacity_rule1)
                # Fixing the generation and capacity of plants that have exceeded their maximum life
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
                    if scenario == "AD":
                        capacity = model.Cap[g, y]
                    elif scenario == "BAU":
                        capacity = model.GenData[g]["CAPACITY"]
                
                    if price_scenario == "AvgPPAPrice":
                        cost_per_mw = model.FC_PPA[g, y]/1000
                    elif price_scenario == "MarketPrice":
                        cost_per_mw = 100
                    cost+=cost_per_mw * capacity
                # year_contribution += -(capacity_sum * price_sum)  # to billion dollars
                
                # Calculate the second part of the objective function
                revenue_sum = 0
                for g in model.g:
                    for t in model.t:
                        revenue_sum +=  (model.rev_unit[g, y, price_scenario] *model.Price_Dist1[y, price_scenario, t]- 
                                        model.cost[g, y])* model.Gen[g, y, t] * model.Price_dur[t]
                        # print(t, model.Gen[g, y, t].value, model.Price_dur[t],model.Price_Dist1[y, price_scenario, t])
                # year_contribution += # to billion dollars
                
                total_objective += model.DR[y]*(revenue_sum*8760 -cost)
            
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
    parser.add_argument('--scenarios', type=str, nargs='+', 
                       default=["AD","BAU"],
                       choices=["BAU", "AD"],
                       help='Scenarios to run.')
    parser.add_argument('--price-scenarios', type=str, nargs='+',
                       default=["AvgPPAPrice", "MarketPrice"],
                       choices=["MarketPrice", "AvgPPAPrice"],
                       help='Price scenarios to run.')
    parser.add_argument('--input-file', type=str,
                       default="InputDataCoalUpdated.xlsx",
                       help='Path to input Excel file.')
    parser.add_argument('--output-file', type=str,
                       default="Results.xlsx",
                       help='Path to output Excel file.')
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

def run_scenario(model_data, scenario, price_scenario, solver):
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
    model.write(f"{scenario}_{price_scenario}.lp", io_options={'symbolic_solver_labels': True})

    result = solver.solve(model, tee=True)
    logging.getLogger('pyomo.core').setLevel(logging.INFO)
    log_infeasible_constraints(model, log_expression=True)    

    log = logging.getLogger('pyomo.core')
    log.setLevel(logging.INFO)

    log_infeasible_constraints(model, log)

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
        print(f"\nModel is infeasible. LP file has been written to {scenario}_{price_scenario}.lp")
        log_infeasible_constraints(model, log_expression=True)
        raise RuntimeError(f"Solver failed for scenario {scenario}_{price_scenario}")
    
    return process_model_results(model)

def check_constraints(model):
    """验证关键约束是否被满足"""
    print("\nConstraint Verification:")
    
    # Check minimum PLF constraints
    for g in model.g:
        for y in model.y:
            plf = sum(
                model.Gen[g, y, t].value * model.Price_dur[t]
                for t in model.t
            ) / (model.Cap[g, y].value * 8760) if model.Cap[g, y].value > 0 else 0
            
            if model.Retire[g, y].value == 0 and plf<0.25:  # 只打印没有退役的电厂
                print(f"Plant {g} Year {y} PLF: {plf:.2f}")
    
    # Check capacity constraints
    for y in model.y:
        total_cap = sum(model.Cap[g, y].value for g in model.g)
        required_cap = model.Price_gen[y][model.s[1]] * 1e6 / (8760 * 0.75)
        if total_cap < required_cap:
            print(f"Year {y} Capacity Check:")
            print(f"  Total: {total_cap:.2f} MW")
            print(f"  Required: {required_cap:.2f} MW")

def main():
    """
    Main function to run the optimization model.
    """
    try:
        # Set up argument parser and parse arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Load and initialize data
        file_path = Path(args.input_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        data = load_excel_data(file_path)
        model_data = initialize_model_data(data)
        
        # Initialize solver
        solver = initialize_solver(args)
        
        # Run scenarios
        results = {}
        for scenario in args.scenarios:
            for price_scenario in args.price_scenarios:
                try:
                    key = f"{scenario}_{price_scenario}"
                    results[key] = run_scenario(model_data, scenario, 
                                             price_scenario, solver)
                    print(f"Successfully completed scenario: {key}")
                except Exception as e:
                    print(f"Error in scenario {key}: {str(e)}")
                    continue
                # Save results
                try:
                    save_results_to_excel(results, args.output_file)
                    print(f"Results saved to {args.output_file}")
                except Exception as e:
                    print(f"Error saving results: {str(e)}")
            
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