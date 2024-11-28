from pyomo.environ import *
from pyomo.opt import SolverFactory
from pathlib import Path
import pandas as pd
from python_version import load_excel_data, initialize_model_data
import argparse

def build_model(model_data, scenario, price_scenario):
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
    model.Price_dur = Param(model.t, initialize=lambda model, t: model_data.price_dur.loc[t, "PercentTime"] if t in model_data.price_dur.index else 0)
    model.Other = Param(model_data.other.index.tolist(), model_data.other.columns.tolist(),
                        initialize=lambda model, k, v: model_data.other.loc[k, v] if (k in model_data.other.index) and (v in model_data.other.columns) else 0)
    model.FC_PPA = Param(model.g, model.y, initialize=lambda model, g, y: model_data.fc_ppa.loc[g, str(y)] if g in model_data.fc_ppa.index and str(y) in model_data.fc_ppa.columns else 0)

    # 定义 price_Dist1 参数
    def price_dist1_init(model, y, p, t):
        if p == "MarketPrice":
            return model.Price_dist[y, t]  #  GAMS Price_Dist(y, t)
        elif p == "AvgPPAPrice":
            return 1  # GAMS Price_Dist1(y, t)
        else:
            return 0  # Default case if needed

    model.Price_Dist1 = Param(model.y, model.p, model.t, initialize=price_dist1_init)
    
    # SetScenario and SetPriceScenario as Boolean Parameters
    model.SetScenario = Param(model.s, initialize=lambda model, s: 1 if s == scenario else 0)
    model.SetPriceScenario = Param(model.p, initialize=lambda model, p: 1 if p == price_scenario else 0)

    # Derived Parameters
    model.DR = Param(model.y, initialize=lambda model, y: 1 / ((1 + model.Other["DiscountRate", "Value"]) ** (y - 2021)))
    model.life = Param(model.g, initialize=lambda model, g: 2021 - model.GenData[g]["STARTYEAR"])
    model.cost = Param(model.g, model.y, initialize=lambda model, g, y: (
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_Lessthan10","Value"]) ** (y - 2021) if model.life[g] < 10 else
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_10-30years","Value"]) ** (y - 2021) if model.life[g] <= 30 else
    model.GenData[g]["AvgPPAPrice"] * 
    (1 + model.Other["CostEsc_30plus","Value"]) ** (y - 2021)
    ))

    def gen_bounds(model, g, y, t):
        max_life = model.Other["MaxLife", "Value"]
        if (y + model.life[g] - 2021) > max_life:
            return (0, 0)  # 下界和上界都为 0，相当于固定为 0
        else:
            return (0, model.GenData[g]["CAPACITY"])  # 最大值为工厂容量

    model.Gen = Var(model.g, model.y, model.t, domain=NonNegativeReals,bounds=gen_bounds)
    # Variables
    model.Cap = Var(model.g, model.y, domain=NonNegativeReals)
    model.Retire = Var(model.g, model.y, domain=Binary)
    model.TotNetRev = Var(domain=Reals)


    def rev_unit_init(model, g, y, price_scenario):
        if price_scenario == "MarketPrice":
            return model.GenData[g]["MarketPrice"]
        elif price_scenario == "AvgPPAPrice":
            return model.GenData[g]["FIXED COST"] + model.cost[g, y]
        else:
            return 0  # Default case if needed

    # model.rev_unit = Constraint(model.g, model.y, model.p, rule=rev_unit_rule)
    model.rev_unit = Param(
        model.g, model.y, model.p,
        initialize=rev_unit_init,
        within=NonNegativeReals
    )
    for g in model.g:
        for y in model.y:
            if y + model.life[g] - 2021 > model.Other['MaxLife', 'Value']:
                model.Cap[g, y].fix(0.0)
                for t in model.t:
                    model.Gen[g, y, t].fix(0.0)

    # Constraints

    # Max Coal Generation
    def max_coal_gen_rule(model, y):
        return sum(
            model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
            for g in model.g for t in model.t
        ) == sum(
            model.Price_gen[y][s] for s in model.s
        )
    model.MaxCoalGen = Constraint(model.y, rule=max_coal_gen_rule)

    # Minimum PLF
    def min_plf_rule(model, g, y):
        return sum(
            model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
            for t in model.t
        ) >= model.Cap[g, y] * 8.76 / 1000 * model.Other["MinPLF", "Value"]
    model.MinPLF = Constraint(model.g, model.y, rule=min_plf_rule)

    # Maximum PLF
    def max_plf_rule(model, g, y):
        return sum(
            model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
            for t in model.t
        ) <= model.Cap[g, y] * 8.76 / 1000 * model.Other["MaxPLF", "Value"]
    model.MaxPLF = Constraint(model.g, model.y, rule=max_plf_rule)

    # Capacity Balance
    def capacity_balance_rule(model, g, y):
        if y == 2021:
            return model.Cap[g, y] == (1- model.Retire[g, y]) * model.GenData[g]["CAPACITY"]
        else:
            return model.Cap[g, y] == model.Cap[g, y-1 ] - model.Retire[g, y] * model.GenData[g]["CAPACITY"]

    model.CapBal = Constraint(model.g, model.y, rule=capacity_balance_rule)
    # Retire Plants
    def max_retire_rule(model, g):
        return sum(
            model.Retire[g, y] for y in model.y
        ) <= 1
    model.MaxRetire = Constraint(model.g, rule=max_retire_rule)

    # Minimum Capacity
    def min_capacity_rule(model, y):
        return sum(
            model.Cap[g, y] for g in model.g
        ) >= model.Price_gen[y][scenario]* 1e6 / (8760 * 0.75)
        
    model.MinCapacity = Constraint(model.y, rule=min_capacity_rule)

    # 定义目标函数
    def objective_rule(model):
        # 折现收益
        return sum(
            model.DR[y] * (
                - sum(
                    (model.GenData[g]["CAPACITY"] * model.SetScenario[s] +
                    model.Cap[g, y] * (1 - model.SetScenario[s])) *
                    (model.FC_PPA[g, y] * model.SetPriceScenario[p] +
                    100 * (1 - model.SetPriceScenario[p]))
                    for g in model.g for s in model.s for p in model.p
                ) / 1e6 +
                sum(
                    (model.rev_unit[g, y, p] * model.Price_Dist1[y, p, t] -
                    model.cost[g, y]) *
                    model.Gen[g, y, t] * model.Price_dur[t] * 8.76 / 1000
                    for g in model.g for p in model.p for t in model.t
                )
            )
            for y in model.y
        )

    model.Obj = Objective(rule=objective_rule, sense=maximize)

    return model


if __name__ == "__main__":
    # Load data and initialize model data
    file_path = Path("InputDataCoalUpdated.xlsx")
    data = load_excel_data(file_path)
    model_data = initialize_model_data(data)
    scenarios = ["BAU","AD"]
    price_scenarios = ["MarketPrice"]#, ["MarketPrice","AvgPPAPrice"]
    # 创建 Argument Parser
    parser = argparse.ArgumentParser(description="Run Pyomo model with solver options.")
    parser.add_argument('--solver', type=str, default='gurobi', help='Solver to use (e.g., glpk, cplex, gurobi).')
    parser.add_argument('--solver-options', type=str, nargs='*', help='Solver options as key=value pairs.')

    # 解析命令行参数
    args = parser.parse_args()

    results = {}

    for scenario in scenarios:
        for price_scenario in price_scenarios:
            # Build the model for the current scenario and price scenario
            model = build_model(model_data, scenario, price_scenario)
            # Comment out constraints for testing
            # model.MinPLF.deactivate()
            # model.MaxPLF.deactivate()
            # model.CapBal.deactivate()
            # 动态选择求解器
            solver = SolverFactory(args.solver)

            # 处理求解器选项
            if args.solver_options:
                options = {k: v for opt in args.solver_options for k, v in [opt.split('=')]}
                for key, value in options.items():
                    solver.options[key] = value

            if solver is None:
                print("Solver not found!")
            else:
                print("Solver is available!")
            result = solver.solve(model, tee=True)
            if (result.solver.status != SolverStatus.ok) or (result.solver.termination_condition != TerminationCondition.optimal):
                print("=====================Solver failed!")
            else:
                print("Solver succeeded!")
            # Extract results
            totgen = {}
            NetRev = {}
            totalCap = {}
            # print("MaxLife:", model.Other["MaxLife", "Value"])
            # for g in model.g:
            #     print(f"Plant {g} life: {model.life[g]}")
            # print(model.Retire.get_values()) 
            for y in model.y:
            #     for g in model.g:
            #         for t in model.t:
            #             print(model.Gen[g, y, t])
                totgen[y] = sum(
                    model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
                    for g in model.g for t in model.t
                )
            SetScenario = 1 if scenario == "BAU"  else 0
            SetPriceScenario = 1 if price_scenario == "MarketPrice" else 0
            for g in model.g:
                for y in model.y:
                    # model.Retire.pprint()
                    fixed_costs = sum(
                        model.GenData[g]['CAPACITY'] *
                        (model.FC_PPA[g, y] * SetPriceScenario +
                        100 * (1 - SetPriceScenario))
                        for p in model.p
                    ) / 1e6
                    variable_revenue = sum(
                        model.Gen[g, y, t].value *
                        model.Price_dist[y, t] *
                        model.Price_dur[t] * 8.76 / 1000
                        for t in model.t
                    )
                    NetRev[g, y] = -fixed_costs + variable_revenue
            for y in model.y:    
                total_capacity_mw = sum(
                                    model.Cap[g, y].value for g in model.g
                                    if model.Cap[g, y].value is not None
                                        )
                # print(f"Total Capacity: {total_capacity_mw}")
                totalCap[y] = total_capacity_mw/1000
            # total_capacity_gw = total_capacity_mw / 1000  #
            # Store results
            print(totalCap)
            key = f"{scenario}_{price_scenario}"
            results[key] = {
                "TotGen": totgen,
                "NetRev": NetRev,
                "TotalNetRevenue": model.TotNetRev.value,
                "total_capacity_gw": totalCap
            }
            retirement_schedule = {}

            for g in model.g:
                retirement_years = []
                for y in model.y:
                    if model.Retire[g, y].value == 1:  # Check if the plant is set to retire in this year
                        retirement_years.append(1)  # Indicate retirement
                    else:
                        retirement_years.append(0)  # Indicate no retirement
                retirement_schedule[g] = retirement_years

    # Save results to Excel
    with pd.ExcelWriter('CoalAnalysisResults_Scenarios.xlsx') as writer:
        for key, result in results.items():
            # Save total generation
            totgen_df = pd.DataFrame.from_dict(result["TotGen"], orient='index', columns=['TotalGeneration'])
            totgen_df.to_excel(writer, sheet_name=f"{key}_TotGen")

            # Save net revenue
            netrev_df = pd.DataFrame.from_dict(result["NetRev"], orient='index')
            netrev_df.to_excel(writer, sheet_name=f"{key}_NetRev")

            # Save total net revenue
            pd.DataFrame([result["TotalNetRevenue"]], columns=['TotalNetRevenue']).to_excel(writer, sheet_name=f"{key}_Summary")
            totcap_df = pd.DataFrame.from_dict(result["total_capacity_gw"], orient='index', columns=['TotalCapacity'])
            totcap_df.to_excel(writer, sheet_name=f"{key}_TotalCapacity")
            
            retirement_df = pd.DataFrame.from_dict(retirement_schedule, orient='index', columns=[str(year) for year in model.y])
            retirement_df.to_excel(writer, sheet_name=f"{key}_RetireSched")
