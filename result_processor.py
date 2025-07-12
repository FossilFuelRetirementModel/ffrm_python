import pandas as pd
from pyomo.core.util import quicksum
from pyomo.environ import value
def process_model_results(model):
    """
    Process the results from a solved model.
    
    Parameters:
    model (ConcreteModel): A solved Pyomo model
    
    Returns:
    dict: Processed results including generation, revenue, and capacity data
    """
    try:
        gen = calculate_total_generation(model)
        # net_rev = calculate_net_revenue(model)
        # total_cap = calculate_total_capacity(model)
        retirement_schedule = calculate_retirement_schedule(model)
        plant_cap = calculate_plant_capacity(model)
        # net_rev = calculate_net_revenue(model)
        annual_summary = calculate_annual_summary(model) 
        plant_netrev = calculate_plant_netrev(model)
        return {
            "PlantGen": gen,
            # "NetRev": net_rev,
            # # "TotalNetRevenue": model.TotNetRev.value,
            # "tot_cap_gw": total_cap,
            "retire_sched": retirement_schedule,
            "plant_cap": plant_cap,
            "AnnualSummary": annual_summary,
            "plant_netrev": plant_netrev
        }
    except Exception as e:
        raise RuntimeError(f"Error processing model results: {str(e)}")

def save_results_to_excel(results, output_file):
    """
    Save the processed results to an Excel file.
    
    Parameters:
    results (dict): The processed results to save
    output_file (str): The path to the output Excel file
    """
    try:
        # Save each scenario's data to separate files
        for key, result in results.items():
            scenario_output_file = f"{key}_results.xlsx"
            with pd.ExcelWriter(scenario_output_file) as scenario_writer:
           
                # Save each component to a separate sheet
                for sheet_name, data in result.items():
                    if sheet_name == "annual_summary":
                        summary_df = pd.DataFrame.from_dict(data, orient='index')
                        summary_df.to_excel(scenario_writer, sheet_name=f"Summary")
                    elif sheet_name == "plant_netrev":
                        # Save annual net revenue
                        annual_df = pd.DataFrame.from_dict(
                            data["annual"], 
                            orient='index'
                        )
                        # Save depreciated capex as an additional column
                        annual_df['Depreciated_Capex_$m'] = data["depreciated_capex"]
                        annual_df.to_excel(scenario_writer, sheet_name=f"PlantNetRev")
                    else:
                        df = pd.DataFrame.from_dict(data, orient='index')
                        df.to_excel(scenario_writer, sheet_name=f"{sheet_name}")            
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.to_excel(scenario_writer, sheet_name=f"{sheet_name}")

                    for sheet_name, data in result.items():
                        df = pd.DataFrame.from_dict(data, orient='index')
                        df.to_excel(scenario_writer, sheet_name=sheet_name)
    except Exception as e:
        raise IOError(f"Error saving results to Excel: {str(e)}")
    try:
        with pd.ExcelWriter(output_file) as writer:
            for key, result in results.items():               
                # Save each component to a separate sheet
                for sheet_name, data in result.items():
                    if sheet_name == "annual_summary":
                        summary_df = pd.DataFrame.from_dict(data, orient='index')
                        summary_df.to_excel(writer, sheet_name=f"{key}_Summary")
                    elif sheet_name == "plant_netrev":
                        # Save annual net revenue
                        annual_df = pd.DataFrame.from_dict(
                            data["annual"], 
                            orient='index'
                        )
                         # Save depreciated capex as an additional column
                        annual_df['Depreciated_Capex_$m'] = data["depreciated_capex"]
                        annual_df.to_excel(writer, sheet_name=f"{key}_PlantNetRev")
                        
                        # # Save depreciated capex
                        # capex_df = pd.DataFrame.from_dict(
                        #     data["depreciated_capex"], 
                        #     orient='index',
                        #     columns=['Depreciated_Capex_$m']
                        # )
                        # capex_df.to_excel(writer, sheet_name=f"{key}_Plant")
                    else:
                        df = pd.DataFrame.from_dict(data, orient='index')
                        df.to_excel(writer, sheet_name=f"{key}_{sheet_name}")
                    # Save each scenario's data to separate files
    except Exception as e:
        raise IOError(f"Error saving results to Excel: {str(e)}")

# def calculate_net_revenue(model):
def calculate_annual_summary(model):
    """
    Calculate annual summary statistics including total generation and net revenue.
    Based on original GAMS code Summary calculations.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Dictionary containing summary statistics by year
    """
    try:
        summary = {}
        plant_netrev = calculate_net_revenue(model)

        for y in model.y:
            summary[y] = {
                # Total Coal Generation (TWh)
                "Total Coal Gen TWh": sum(
                    model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
                    for g in model.g 
                    for t in model.t
                ),
                
                # Total Capacity (GW)
                "Total Capacity GW": sum(
                    model.Cap[g, y].value for g in model.g
                ) / 1000,
                
                # Total Undiscounted Net Revenue ($b)
                "Total Undiscounted Net Revenue $b":
                   sum(
                    plant_netrev[g][y] for g in model.g
                ) / 1000  ,# Convert to billions
                "Discounted Net Revenue $b": sum(
                    plant_netrev[g][y] * model.DR[y] for g in model.g
                ) / 1000  # Convert to billions
                }
        
        return summary
    except Exception as e:
        raise RuntimeError(f"Error calculating annual summary: {str(e)}")

def calculate_plant_netrev(model):
    """
    Calculate net revenue for each plant and year.
    Based on original GAMS code NetRev calculations.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Dictionary containing plant net revenue and depreciated capex
    """
    try:
        plant_netrev = {"annual": {}, "depreciated_capex": {}}
        
        # Calculate annual net revenue for each plant
        for g in model.g:
            plant_netrev["annual"][g] = {}
            for y in model.y:
                # Calculate net revenue according to GAMS formula
                '''
                if y ==2021:
                    print("--------------------------------")
                    print('BAU',model.GenData[g]["CAPACITY"])
                    print('AD',model.Cap[g, y].value)
                    print(model.GenData[g]["CAPACITY"] * model.SetScenario[model.s[1]] +
                        model.Cap[g, y].value * (1 - model.SetScenario[model.s[1]]))
                    print('Gen',sum(model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 for t in model.t))
                    print('PPA',model.FC_PPA[g, y])
                    print('SetScenario', [model.SetScenario[s] for s in model.s])
                    print('SetPriceScenario', [model.SetPriceScenario[p] for p in model.p])
                    print("--------------------------------") 
                    print
                '''
                netrev = -(
                            # Use the corresponding capacity based on scenario
                            model.Cap[g, y].value if model.s.at(1) == "AD" else model.GenData[g]["CAPACITY"]
                        ) *(
                            # Use the corresponding price based on price scenario
                            model.FC_PPA[g, y]/1e3 if model.p.at(1) == "AvgPPAPrice" else 100
                        ) + quicksum(
                        (
                            model.rev_unit[g, y, model.p.at(1)] * 
                            model.Price_Dist1[y, model.p.at(1), t] - 
                            model.cost[g, y]
                        ) * model.Gen[g, y, t].value * model.Price_dur[t] * 8760
                        for t in model.t
                    )
               
                plant_netrev["annual"][g][y] = netrev/1e6
            
            # Calculate depreciated capex
            plant_netrev["depreciated_capex"][g] = max(
                model.GenData[g]["CAPACITY"] * 
                model.Other["CoalCapex", "Value"] * 
                (1 - model.Other["SLD", "Value"] * model.life[g]), 
                0
            ) / 1000
        print(model.p[1])
        return plant_netrev
    except Exception as e:
        raise RuntimeError(f"Error calculating plant net revenue: {str(e)}")

def calculate_annual_total_netrev(model):
    """
    Calculate total net revenue for each year (both nominal and discounted).
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Dictionary containing nominal and discounted net revenue by year
    """
    try:
        annual_netrev = {"nominal": {}, "discounted": {}}
        
        # Use the existing calculate_net_revenue function to get the net revenue for each plant
        plant_netrev = calculate_net_revenue(model)
        
        # Get all years
        years = list(plant_netrev[list(plant_netrev.keys())[0]].keys())
        
        # Calculate total net revenue for each year
        for year in years:
            # Calculate nominal value: sum of net revenue for all plants in the year
            annual_netrev["nominal"][year] = sum(
                plant_netrev[plant][year] 
                for plant in plant_netrev.keys()
            )
            
            # 计算折现值：使用相同的折现率(10%)
            annual_netrev["discounted"][year] = (
                annual_netrev["nominal"][year] / 
                (1 + 0.06) ** (int(year) - 2021)  # 假设基准年为2021，折现率为10%
            )

        return annual_netrev
    except Exception as e:
        raise RuntimeError(f"Error calculating annual total net revenue: {str(e)}")

def calculate_total_generation(model):
    """
    Calculate total generation for each plant and year.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Total generation by plant and year in TWh
    """
    try:
        gen = {}
        '''
        for g in model.g:
            total_gen[g] = {}
            for y in model.y:
                # Sum generation across all time blocks and convert to TWh
                total_gen[g][y] = sum(
                    model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000 
                    for t in model.t
                )
        '''
        for g in model.g:
            gen[g] = {}
            for y in model.y:
            #         for t in model.t:
            #             print(model.Gen[g, y, t])
                gen[g][y] = round(sum(
                    model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 for t in model.t),5)
        
        return gen
    except Exception as e:
        raise RuntimeError(f"Error calculating total generation: {str(e)}")

def calculate_net_revenue(model):
    """
    Calculate net revenue for each plant and year.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Net revenue by plant and year in millions of currency units
    """
    try:
        net_revenue = calculate_plant_netrev(model)["annual"]
        return net_revenue
    except Exception as e:
        raise RuntimeError(f"Error calculating net revenue: {str(e)}")

def calculate_total_capacity(model):
    """
    Calculate total capacity for each plant and year.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Total capacity by plant and year in GW
    """
    try:
        total_capacity = {}
        for y in model.y:    
            total_capacity_mw = sum(
                model.Cap[g, y].value for g in model.g
            )
            # print(f"Total Capacity: {total_capacity_mw}")
            total_capacity[y] = total_capacity_mw/1000
        # print(total_capacity)
        return total_capacity
    except Exception as e:
        raise RuntimeError(f"Error calculating total capacity: {str(e)}")
    
def calculate_plant_capacity(model):
    """
    Calculate capacity for each plant and year.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Capacity by plant and year in MW
    """
    try:
        plant_capacity = {}
        for g in model.g:
            plant_capacity[g] = {}
            for y in model.y:
                plant_capacity[g][y] = model.Cap[g, y].value
        return plant_capacity
    except Exception as e:
        raise RuntimeError(f"Error calculating plant capacity: {str(e)}")


def calculate_retirement_schedule(model):
    """
    Calculate retirement schedule for each plant.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Retirement schedule by plant and year (1 if retired, 0 if operating)
    """
    try:
        retirement = {}
        for g in model.g:
            retirement[g] = {}
            for y in model.y:
                retirement[g][y] = model.Retire[g, y].value
        return retirement
    except Exception as e:
        raise RuntimeError(f"Error calculating retirement schedule: {str(e)}")