from pyomo.environ import value, Constraint, Var, ConcreteModel

def validate_retirement_economics(model):
    """检查每个电厂退役的经济性"""
    for g in model.g:
        for y in model.y:
            if value(model.Retire[g, y]) > 0.5:  # 如果退役了
                # 计算继续运营的收益
                revenue = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) * 
                    value(model.rev_unit[g, y, p] * model.Price_Dist1[y, p, t] - model.cost[g, y])
                    for t in model.t for p in model.p if value(model.SetPriceScenario[p])
                )
                
                # 计算容量支付成本
                capacity_payment = sum(
                    value(model.GenData[g]["CAPACITY"]) * 
                    (value(model.FC_PPA[g, y]) * value(model.Index[p]) + 100 * (1-value(model.Index[p])))
                    for p in model.p
                ) / 1e6
                
                print(f"\nPlant {g} retired in year {y}:")
                print(f"  Revenue potential: {revenue:,.2f}")
                print(f"  Capacity payment: {capacity_payment:,.2f}")
                
def check_capacity_constraints(model):
    """验证容量约束的执行"""
    for y in model.y:
        total_cap = sum(value(model.Cap[g, y]) for g in model.g)
        min_req = value(model.Price_gen[y][model.scenario]) * 1e6 / (8760 * 0.75)
        margin = total_cap - min_req
        
        print(f"\nYear {y}:")
        print(f"  Total Capacity: {total_cap:,.2f} MW")
        print(f"  Minimum Required: {min_req:,.2f} MW")
        print(f"  Margin: {margin:,.2f} MW")
        
def check_plf_constraints(model):
    """检查PLF约束的实际值"""
    for g in model.g:
        for y in model.y:
            if value(model.Cap[g, y]) > 0:
                gen_sum = sum(
                    value(model.Gen[g, y, t]) * value(model.Price_dur[t]) * 8.76 / 1000
                    for t in model.t
                )
                plf = gen_sum / (value(model.Cap[g, y]) * 8.76 / 1000)
                
                if plf < value(model.Other["MinPLF", "Value"]) - 1e-6:
                    print(f"Warning: Plant {g} Year {y} PLF {plf:.3f} below minimum")
def verify_cost_calculations(model):
    """验证成本计算"""
    for g in model.g:
        for y in model.y:
            # 计算GAMS版本的成本
            gams_cost = 0
            if model.life[g] < 10:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.Other["CostEsc_Lessthan10","Value"]) ** (y - 2021))
            elif model.life[g] <= 30:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.Other["CostEsc_10-30years","Value"]) ** (y - 2021))
            else:
                gams_cost = (model.GenData[g]["COST"] * 
                           (1 + model.Other["CostEsc_30plus","Value"]) ** (y - 2021))
            
            # 比较与模型中的成本
            model_cost = value(model.cost[g, y])
            if abs(gams_cost - model_cost) > 1e-6:
                print(f"Cost mismatch for Plant {g} Year {y}:")
                print(f"  GAMS: {gams_cost:.2f}")
                print(f"  Model: {model_cost:.2f}")