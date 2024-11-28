from pyomo.environ import *
from pyomo.opt import SolverFactory
from pathlib import Path
import pandas as pd
from energy_data_processor import load_excel_data, initialize_model_data
from result_processor import process_model_results, save_results_to_excel
import argparse

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
        # model.s = Set(initialize=model_data.scenarios.keys())
        # model.p = Set(initialize=model_data.price_scenarios.keys())
        model.s = Set(initialize={scenario})
        model.p = Set(initialize={price_scenario})
        
        # Parameters
        model.GenData = Param(model.g, initialize=model_data.gen_data.to_dict('index'))
        model.Price_gen = Param(model.y, initialize=model_data.price_gen.to_dict('index'))
        model.Price_dist = Param(model.y, model.t, initialize=model_data.price_dist.stack().to_dict())
        
        model.Price_dur = Param(
            model.t, 
            initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] 
            if t in model_data.price_dur.index else 0
            )
        
        model.Other = Param(
            model_data.other.index.tolist(), 
            model_data.other.columns.tolist(),
            initialize=lambda model, k, v: model_data.other.loc[k, v] 
            if (k in model_data.other.index) and (v in model_data.other.columns) else 0
            )
        
        model.FC_PPA = Param(
            model.g, model.y, 
            initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] 
            if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else 0
            )

        # Define price_Dist1 parameter, this parameter is used classify different price scenarios
        def price_dist1_init(model, y, p, t):
            """
            Initialize the price distribution parameter based on the price scenario.

            Returns: float: The price distribution value based on the scenario.
            """
            if p == "MarketPrice":
                return model.Price_dist[y, t]  #  GAMS Price_Dist(y, t)
            elif p == "AvgPPAPrice":
                return 1  
            else:
                return 0  # Default case if needed

        model.Price_Dist1 = Param(model.y, model.p, model.t, initialize=price_dist1_init)
        
        # Scenario and PriceScenario as Boolean Parameters
        # BAU = 1, AD = 0
        ############################################################
        # Here we have a possible error in the code,
        ############################################################
        model.SetScenario = Param(model.s, initialize=lambda model, s: 1 if s == "BAU" else 0)
        # MarketPrice = 1, AvgPPAPrice = 0
        model.SetPriceScenario = Param(model.p, initialize=lambda model, p: 1 if p == "MarketPrice" else 0)


        # We now compute those derived Parameters
        model.DR = Param(
            model.y, 
            initialize=lambda model, 
            y: 1 / (1 + model.Other["DiscountRate", "Value"]) ** (y - 2021)
            )
        
        model.life = Param(
            model.g, 
            initialize=lambda model, 
            g: 2021 - model.GenData[g]["STARTYEAR"]
            )
        
        model.cost = Param(
            model.g, model.y, 
            initialize=lambda model, g, y: (
                                    model.GenData[g]["COST"] * 
                                    (1 + model.Other["CostEsc_Lessthan10","Value"]) ** (y - 2021) if model.life[g] < 10 else
                                    model.GenData[g]["COST"] * 
                                    (1 + model.Other["CostEsc_10-30years","Value"]) ** (y - 2021) if model.life[g] <= 30 else
                                    model.GenData[g]["COST"] * 
                                    (1 + model.Other["CostEsc_30plus","Value"]) ** (y - 2021)
                                    )
                                )


        # Variables
        def calculate_generation_bounds(model, g, y, t):
            '''
            This function is used to set the bounds for the 'generation' variable, model.Gen
            '''
            max_life = model.Other["MaxLife", "Value"]
            if (y + model.life[g] - 2021) > max_life:
                return (0, 0)  
            else:
                return (0, model.GenData[g]["CAPACITY"])  

        model.Gen = Var(model.g, model.y, model.t, domain=NonNegativeReals,bounds=calculate_generation_bounds)
        model.Cap = Var(model.g, model.y, domain=NonNegativeReals)
        model.Retire = Var(model.g, model.y, domain=Binary)
        model.TotNetRev = Var(domain=Reals)
        

        def rev_unit_init(model, g, y, price_scenario):
            '''
            Here we initialize the revenue unit of generation based on the price scenario
            '''
            if price_scenario == "MarketPrice":
                return model.GenData[g]["MarketPrice"]
            elif price_scenario == "AvgPPAPrice":
                return model.GenData[g]["FIXED COST"] + model.cost[g, y]
                ############################################################
                # IS "FIXED COST" Correct? Should it be "AvgPPAPrice"?
                ############################################################
            else:
                return 0  # Default case if needed

        # model.rev_unit = Constraint(model.g, model.y, model.p, rule=rev_unit_rule)
        model.rev_unit = Param(
            model.g, model.y, model.p,
            initialize=rev_unit_init,
            within=NonNegativeReals
            )
        
        # Fixing the generation and capacity of plants that have exceeded their maximum life
        for g in model.g:
            for y in model.y:
                if y + model.life[g] - 2021 > model.Other['MaxLife', 'Value']:
                    model.Cap[g, y].fix(0.0)
                    for t in model.t:
                        model.Gen[g, y, t].fix(0.0)
        #####################################################################################

        ##### Constraints
        def max_coal_gen_rule(model, y):
            '''
            This function is used to set the maximum generation of coal plants
            '''
            return sum(
                model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
                for g in model.g for t in model.t
                    ) == sum(
                model.Price_gen[y][s] for s in model.s
                    )
        model.MaxCoalGen = Constraint(model.y, rule=max_coal_gen_rule)

        # Minimum PLF
        def min_plf_rule(model, g, y):
            """
            This function is used to set the MINIMUM PLF rule
            """
            return sum(
                model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
                for t in model.t
            ) >= model.Cap[g, y] * 8.76 / 1000 * model.Other["MinPLF", "Value"]
            
        model.MinPLF = Constraint(model.g, model.y, rule=min_plf_rule)

        # Maximum PLF
        def max_plf_rule(model, g, y):
            """
            This function is used to set the MAXIMUM PLF rule
            """
            return sum(
                model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
                for t in model.t
            ) <= model.Cap[g, y] * 8.76 / 1000 * model.Other["MaxPLF", "Value"]
        model.MaxPLF = Constraint(model.g, model.y, rule=max_plf_rule)

        # Capacity Balance
        def capacity_balance_rule(model, g, y):
            """
            This function is used to set the CAPACITY BALANCE rule
            """
            if y == 2021:
                return model.Cap[g, y] == (1- model.Retire[g, y]) * model.GenData[g]["CAPACITY"]
            else:
                return model.Cap[g, y] == model.Cap[g, y-1] - model.Retire[g, y] * model.GenData[g]["CAPACITY"]

        model.CapBal = Constraint(model.g, model.y, rule=capacity_balance_rule)
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
            return sum(
                model.Cap[g, y] for g in model.g
            ) >= model.Price_gen[y][scenario]* 1e6 / (8760 *0.75)
            
        model.MinCapacity = Constraint(model.y, rule=min_capacity_rule)

        # 定义目标函数
        def objective_rule(model):
            """
            This function is used to set the OBJECTIVE function
            """
            return sum(
                model.DR[y] * (
                    - sum(
                            (
                                #Universal Expression for both BAU and AD
                                #For BAU, use the capacity from GenData, as SetScenario = 1
                                model.GenData[g]["CAPACITY"] * model.SetScenario[scenario] +
                                #For AD, use the capacity from Cap, as SetScenario = 0
                                model.Cap[g, y] * (1 - model.SetScenario[scenario])
                            ) 
                            *
                            (
                                #Universal Expression for both MarketPrice and AvgPPAPrice
                                #For MarketPrice, use the PPA from FC_PPA, as SetPriceScenario = 1
                                model.FC_PPA[g, y] * model.SetPriceScenario[price_scenario] +
                                #For AvgPPAPrice, use 100, as SetPriceScenario = 0
                                100 * (1 - model.SetPriceScenario[price_scenario])
                            )
                            for g in model.g #for s in model.s for p in model.p
                        ) / 1e6 #Divide by 1e6 to convert from MWh to TWh
                    + sum(
                        ( 
                            model.rev_unit[g, y, p] * model.Price_Dist1[y, p, t] - model.cost[g, y]
                        ) 
                        * model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
                        for g in model.g for t in model.t for p in model.p
                        )
                )
                for y in model.y
                )

        model.Obj = Objective(rule=objective_rule, sense=maximize)

        return model
    
    except Exception as e:
        raise RuntimeError(f"Error creating optimization model: {str(e)}")
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
                       default=["BAU"],
                       choices=["BAU", "AD"],
                       help='Scenarios to run.')
    parser.add_argument('--price-scenarios', type=str, nargs='+',
                       default=["MarketPrice"],
                       choices=["MarketPrice", "AvgPPAPrice"],
                       help='Price scenarios to run.')
    parser.add_argument('--input-file', type=str,
                       default="InputDataCoalUpdated.xlsx",
                       help='Path to input Excel file.')
    parser.add_argument('--output-file', type=str,
                       default="CoalAnalysisResults_Scenarios.xlsx",
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
    solver = SolverFactory(args.solver)
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
    model = build_model(model_data, scenario, price_scenario)
    result = solver.solve(model, tee=True)
    
    if (result.solver.status != SolverStatus.ok) or \
       (result.solver.termination_condition != TerminationCondition.optimal):
        raise RuntimeError(f"Solver failed for scenario {scenario}_{price_scenario}")
    
    return process_model_results(model)

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


if __name__ == "__main__":
    main()
    # try:
    #     # Load data and initialize model data
    #     file_path = Path("InputDataCoalUpdated.xlsx")
    #     if not file_path.exists():
    #         raise FileNotFoundError(f"Input file not found: {file_path}")
        
    #     data = load_excel_data(file_path)
    #     model_data = initialize_model_data(data)
        
    #     # Argument Parser for solver options
    #     parser = argparse.ArgumentParser(description="Run Pyomo model with solver options.")
    #     parser.add_argument('--solver', type=str, default='gurobi', 
    #                         choices=['glpk', 'cplex', 'gurobi', 'cbc'],
    #                         help='Solver to use (e.g., glpk, cplex, gurobi, cbc).')
    #     parser.add_argument('--solver-options', type=str, nargs='*',
    #                         help='Solver options as key=value pairs.')

    #     # Parse command line arguments
    #     args = parser.parse_args()

    #     # Solver validation
    #     solver = SolverFactory(args.solver)
    #     if solver is None:
    #         raise RuntimeError(f"Solver {args.solver} not available")
        
    #     # Handle solver options from command line, default is Gurobi
    #     if args.solver_options:
    #         options = {k: v for opt in args.solver_options for k, v in [opt.split('=')]}
    #         for key, value in options.items():
    #             solver.options[key] = value
                      
    #     # Scenarios and PriceScenarios
    #     ## This should be add to the argument parser in the future
    #     scenarios = ["BAU"] # ["BAU", "AD"]
    #     price_scenarios = ["MarketPrice"]#, ["MarketPrice","AvgPPAPrice"]
        
    #     results = {}

    #     for scenario in scenarios:
    #         for price_scenario in price_scenarios:
    #             # Build the model for the current scenario and price scenario
    #             try:
    #                 model = build_model(model_data, scenario, price_scenario)
    #                 # Comment out constraints for testing
    #                 # model.MinPLF.deactivate()
    #                 # model.MaxPLF.deactivate()
    #                 # model.CapBal.deactivate()

    #                 result = solver.solve(model, tee=True)
                    
    #                 # Validate solution
    #                 if (result.solver.status != SolverStatus.ok) or \
    #                     (result.solver.termination_condition != TerminationCondition.optimal):
    #                     print (f"Solver failed for scenario {scenario}_{price_scenario}")
    #                 # Process results/Extract Some of the results
    #                 key = f"{scenario}_{price_scenario}"
    #                 results[key] = process_model_results(model)
                    
    #             except Exception as e:
    #                 print(f"Error building model for scenario {scenario}_{price_scenario}: {str(e)}")
    #                 continue
                                    
    #             # Save results
    #             try:
    #                 save_results_to_excel(results, 'CoalAnalysisResults_Scenarios.xlsx')
    #             except Exception as e:
    #                 print(f"Error saving results: {str(e)}")
    # except Exception as e:
    #     print(f"Fatal error: {str(e)}")