from pyomo.environ import value, Constraint, Var, ConcreteModel

def validate_retirement_economics(model):
    """Validate retirement economics for each plant."""
    for g in model.g:
        for y in model.y:
            if value(model.Retire[g, y]) > 0.5:  # retired
                # Calculate revenue potential from continued operation
                revenue = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) * 
                    value(model.rev_unit[g, y, p] * model.Price_Dist1[y, p, t] - model.cost[g, y])
                    for t in model.t for p in model.p if value(model.SetPriceScenario[p])
                )
                
                # Calculate capacity payment cost
                capacity_payment = sum(
                    value(model.GenData[g]["CAPACITY"]) * 
                    (value(model.FC_PPA[g, y]) * value(model.Index[p]) + 100 * (1-value(model.Index[p])))
                    for p in model.p
                ) / 1e6
                
                print(f"\nPlant {g} retired in year {y}:")
                print(f"  Revenue potential: {revenue:,.2f}")
                print(f"  Capacity payment: {capacity_payment:,.2f}")
                
def check_capacity_constraints(model):
    """Validate capacity constraint behavior."""
    for y in model.y:
        total_cap = sum(value(model.Cap[g, y]) for g in model.g)
        min_req = value(model.Price_gen[y][model.scenario]) * 1e6 / (8760 * 0.75)
        margin = total_cap - min_req
        
        print(f"\nYear {y}:")
        print(f"  Total Capacity: {total_cap:,.2f} MW")
        print(f"  Minimum Required: {min_req:,.2f} MW")
        print(f"  Margin: {margin:,.2f} MW")
        
def check_plf_constraints(model):
    """Check actual PLF values against constraints."""
    for g in model.g:
        for y in model.y:
            if value(model.Cap[g, y]) > 0:
                gen_sum = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) * 8.76 / 1000
                    for t in model.t
                )
                plf = gen_sum / (value(model.Cap[g, y]) * 8.76 / 1000)
                
                # Get technology type for this plant
        tech_type = value(model.GenData[g]["TECHNOLOGY"])
        if plf < value(model.TechParams[tech_type, "MinPLF"]) - 1e-6:
                    print(f"Warning: Plant {g} Year {y} PLF {plf:.3f} below minimum")
def verify_cost_calculations(model):
    """Verify cost calculations."""
    for g in model.g:
        for y in model.y:
            # Calculate GAMS-style cost
            gams_cost = 0
            # Use dynamic base year from model data
            base_year = min(model.y)
            # Get technology type for this plant
            tech_type = value(model.GenData[g]["TECHNOLOGY"])
            if model.life[g] < 10:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.TechParams[tech_type,"CostEsc_Lessthan10"]) ** (y - base_year))
            elif model.life[g] <= 30:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.TechParams[tech_type,"CostEsc_10-30years"]) ** (y - base_year))
            else:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.TechParams[tech_type,"CostEsc_30plus"]) ** (y - base_year))
            
            # Compare with model cost
            model_cost = value(model.cost[g, y])
            if abs(gams_cost - model_cost) > 1e-6:
                print(f"Cost mismatch for Plant {g} Year {y}:")
                print(f"  GAMS: {gams_cost:.2f}")
                print(f"  Model: {model_cost:.2f}")