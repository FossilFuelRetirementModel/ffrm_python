import pyomo.environ as pyo

def create_model():
    model = pyo.ConcreteModel()
    
    # Define your sets
    model.y = pyo.Set(initialize=range(2021, 2041))  # years 2021-2040
    model.g = pyo.Set()  # your generators set
    model.t = pyo.Set()  # timeblocks
    
    # Define scenario sets and parameters
    model.s = pyo.Set(initialize=['BAU', 'AD'])
    model.p = pyo.Set(initialize=['MarketPrice', 'AvgPPAPrice'])
    
    # Scenario control parameters
    model.SetScenario = pyo.Param(
        model.s, 
        initialize={'BAU': 1, 'AD': 0},
        mutable=True
    )
    
    model.SetPriceScenario = pyo.Param(
        model.p,
        initialize={'MarketPrice': 1, 'AvgPPAPrice': 0},
        mutable=True
    )
    
    # Define revenue parameters similar to your GAMS code
    # rev_unit(g,y,"MarketPrice") = GenData(g,"MarketPrice")
    # rev_unit(g,y,"AvgPPAPrice") = GenData(g,"FIXED COST") + Cost(g,y)
    model.rev_unit = pyo.Param(
        model.g, 
        model.y, 
        model.p, 
        mutable=True
    )
    
    # Price distribution parameters similar to your GAMS code
    # price_Dist1(y,"MarketPrice",t) = Price_Dist(y,t)
    # price_Dist1(y,"AvgPPAPrice",t) = 1
    model.price_dist1 = pyo.Param(
        model.y,
        model.p,
        model.t,
        initialize=lambda m, y, p, t: (
            m.Price_Dist[y,t] if p == 'MarketPrice' else 1
        ),
        mutable=True
    )
    
    # Variables
    model.Gen = pyo.Var(model.g, model.y, model.t, domain=pyo.NonNegativeReals)
    
    # Objective function incorporating both scenarios and price types
    def obj_rule(m):
        return sum(
            m.DR[y] * (
                # Cost term
                -sum(
                    sum(
                        m.SetScenario[s] * (
                            m.GenData[g,'Capacity'] * m.Flag[s] +
                            m.Cap[g,y] * (1-m.Flag[s])
                        ) * (
                            m.FC_PPA[g,y] * m.index[p] +
                            100 * (1-m.index[p])
                        )
                        for s in m.s
                    ) for p in m.p
                ) / 1e6 +
                # Revenue term
                sum(
                    sum(
                        m.SetPriceScenario[p] * (
                            (m.rev_unit[g,y,p] * m.price_dist1[y,p,t] - m.Cost[g,y]) *
                            m.Gen[g,y,t] * m.Price_Dur[t,'PercentTime'] * 8.76/1000
                        ) for t in m.t
                    ) for p in m.p for g in m.g
                )
            ) for y in m.y
        )
    
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
    
    return model

# Usage:
def solve_model_both_scenarios():
    # First solve BAU scenario
    model = create_model()
    model.SetScenario['BAU'] = 1
    model.SetScenario['AD'] = 0
    model.SetPriceScenario['MarketPrice'] = 1
    model.SetPriceScenario['AvgPPAPrice'] = 0
    
    # Solve BAU scenario
    solver = pyo.SolverFactory('your_solver')  # e.g., 'gurobi', 'cplex', etc.
    results_bau = solver.solve(model)
    
    # Store BAU results
    bau_results = {
        'objective': pyo.value(model.objective),
        'generation': {(g,y,t): pyo.value(model.Gen[g,y,t]) 
                      for g in model.g 
                      for y in model.y 
                      for t in model.t}
    }
    
    # Switch to AD scenario
    model.SetScenario['BAU'] = 0
    model.SetScenario['AD'] = 1
    
    # Solve AD scenario
    results_ad = solver.solve(model)
    
    # Store AD results
    ad_results = {
        'objective': pyo.value(model.objective),
        'generation': {(g,y,t): pyo.value(model.Gen[g,y,t]) 
                      for g in model.g 
                      for y in model.y 
                      for t in model.t}
    }
    
    return bau_results, ad_results
# Example of changing price scenarios
def run_sensitivity():
    model = create_model()
    
    # Market Price with BAU
    model.SetScenario['BAU'] = 1
    model.SetPriceScenario['MarketPrice'] = 1
    
    # PPA Price with BAU
    model.SetPriceScenario['MarketPrice'] = 0
    model.SetPriceScenario['AvgPPAPrice'] = 1
    
    # Market Price with AD
    model.SetScenario['BAU'] = 0
    model.SetScenario['AD'] = 1
    model.SetPriceScenario['MarketPrice'] = 1
    
    # PPA Price with AD
    model.SetPriceScenario['MarketPrice'] = 0
    model.SetPriceScenario['AvgPPAPrice'] = 1