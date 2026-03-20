from pyomo.environ import value, Constraint, Var, ConcreteModel
from config import Config

def validate_retirement_economics(model):
    """Validate retirement economics for each plant."""
    for g in model.g:
        for y in model.y:
            if value(model.Retire[g, y]) > 0.5:  # retired
                # Calculate revenue potential from continued operation
                revenue = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) *
                    value(model.rev_unit[g, y, model.p.at(1)] * model.Price_Dist1[y, model.p.at(1), t] - model.cost[g, y])
                    for t in model.t
                )

                # Calculate capacity payment cost (using PPA price scenario if active)
                p = model.p.at(1)
                if p == "AvgPPAPrice":
                    cost_per_mw = value(model.FC_PPA[g, y]) / Config.USD_TO_THOUSANDS
                else:
                    cost_per_mw = Config.DEFAULT_COST_PER_MW_MarketPrice
                capacity_payment = value(model.GenData[g]["CAPACITY"]) * cost_per_mw / Config.USD_TO_MILLIONS

                print(f"\nPlant {g} retired in year {y}:")
                print(f"  Revenue potential: {revenue:,.2f}")
                print(f"  Capacity payment: {capacity_payment:,.2f}")

def check_capacity_constraints(model):
    """Validate capacity constraint behavior."""
    for y in model.y:
        total_cap = sum(value(model.Cap[g, y]) for g in model.g)
        # Estimate minimum required capacity from per-technology generation targets
        required_cap = sum(
            value(model.PriceGenTech[y, tech]) * Config.USD_TO_MILLIONS /
            (Config.HOURS_PER_YEAR * Config.MAX_LOAD_FACTOR)
            for tech in model.tech
        )
        margin = total_cap - required_cap

        print(f"\nYear {y}:")
        print(f"  Total Capacity: {total_cap:,.2f} MW")
        print(f"  Estimated Required: {required_cap:,.2f} MW")
        print(f"  Margin: {margin:,.2f} MW")

def check_plf_constraints(model):
    """Check actual PLF values against constraints."""
    for g in model.g:
        for y in model.y:
            if value(model.Cap[g, y]) > 0:
                gen_sum = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) * Config.HOURS_PER_YEAR / Config.USD_TO_THOUSANDS
                    for t in model.t
                )
                plf = gen_sum / (value(model.Cap[g, y]) * Config.HOURS_PER_YEAR / Config.USD_TO_THOUSANDS)

                # Get technology type for this plant
                tech_type = value(model.GenData[g]["TECHNOLOGY"])
                if plf < value(model.TechParams[tech_type, "MinPLF"]) - Config.TOLERANCE:
                    print(f"Warning: Plant {g} Year {y} PLF {plf:.3f} below minimum")
def verify_cost_calculations(model):
    """Verify cost calculations."""
    for g in model.g:
        for y in model.y:
            # Calculate GAMS-style cost
            gams_cost = 0
            # Use Config.BASE_YEAR consistent with cost parameter initialization
            base_year = Config.BASE_YEAR
            # Get technology type for this plant
            tech_type = value(model.GenData[g]["TECHNOLOGY"])
            if model.life[g] < Config.YOUNG_PLANT_THRESHOLD:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.TechParams[tech_type,"CostEsc_Lessthan10"]) ** (y - base_year))
            elif model.life[g] <= Config.OLD_PLANT_THRESHOLD:
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