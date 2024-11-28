import pandas as pd

def process_model_results(model):
    """
    Process the results from a solved model.
    
    Parameters:
    model (ConcreteModel): A solved Pyomo model
    
    Returns:
    dict: Processed results including generation, revenue, and capacity data
    """
    try:
        totgen = calculate_total_generation(model)
        net_rev = calculate_net_revenue(model)
        total_cap = calculate_total_capacity(model)
        retirement_schedule = calculate_retirement_schedule(model)
        
        return {
            "TotGen": totgen,
            "NetRev": net_rev,
            # "TotalNetRevenue": model.TotNetRev.value,
            "tot_cap_gw": total_cap,
            "retire_sched": retirement_schedule
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
        with pd.ExcelWriter(output_file) as writer:
            for key, result in results.items():
                # Save each component to a separate sheet
                for sheet_name, data in result.items():
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.to_excel(writer, sheet_name=f"{key}_{sheet_name}")
    except Exception as e:
        raise IOError(f"Error saving results to Excel: {str(e)}")
    

def calculate_total_generation(model):
    """
    Calculate total generation for each plant and year.
    
    Parameters:
    model (ConcreteModel): The solved Pyomo model
    
    Returns:
    dict: Total generation by plant and year in TWh
    """
    try:
        total_gen = {}
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
        for y in model.y:
            #     for g in model.g:
            #         for t in model.t:
            #             print(model.Gen[g, y, t])
                total_gen[y] = sum(
                    model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
                    for g in model.g for t in model.t
                )
        return total_gen
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
        net_revenue = {}
        for g in model.g:
            net_revenue[g] = {}
            for y in model.y:
                revenue = sum(
                    (
                        model.rev_unit[g, y, p] * 
                        model.Price_Dist1[y, p, t] - 
                        model.cost[g, y]
                    ) * model.Gen[g, y, t].value * model.Price_dur[t] * 8.76 / 1000
                    for t in model.t
                    for p in model.p
                )
                net_revenue[g][y] = revenue
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
        '''
        for g in model.g:
            total_capacity[g] = {}
            for y in model.y:
                total_capacity[g][y] = model.Cap[g, y].value
        '''
        for y in model.y:    
            total_capacity_mw = sum(
                model.Cap[g, y].value for g in model.g
                if model.Cap[g, y].value is not None
            )
            # print(f"Total Capacity: {total_capacity_mw}")
            total_capacity[y] = total_capacity_mw/1000
        print(total_capacity)
        return total_capacity
    except Exception as e:
        raise RuntimeError(f"Error calculating total capacity: {str(e)}")

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