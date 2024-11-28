// ====================================================================
// Stranded Asset Compensation Calculations
// ====================================================================

option optcr=0.06;    // 设置优化收敛准则（相对 MIP 间隙）。

// 定义集合
Sets
    g / /                  // 发电厂集合。
    y /2021*2040/          // 年份集合，从 2021 到 2040。
    t / /                  // 一年内的时间段集合。
    s scenarios /BAU, AD/  // 情景集合：BAU（常规情景）和 AD（加速去碳情景）。
    p price scenarios /MarketPrice, AvgPPAPrice/ // 价格情景：市场价格和 PPA 平均价格。
;

// 情景和价格情景的参数设置
Parameter
    SetScenario(s) /BAU 1, AD 0/     // 初始情景为 BAU。
    SetPriceScenario(p) /MarketPrice 1, AvgPPAPrice 0/  // 初始价格情景为市场价格。
;

// 定义输入数据的参数
Parameters
    GenData(g,*)          // 发电厂级别数据（容量、成本等）。
    Price_gen(y,*)        // 按年份的平均价格和煤炭发电预测。
    Price_dist(y,t)       // 价格分布，表示为平均价格的倍数。
    Price_dur(t,*)        // 一年内价格区间的持续时间。
    Other(*,*)            // 其他参数（如折现率、成本增长率）。
    FC_PPA(g,y)           // 强制固定容量支付，按 85% PLF 在 25 年期间计算。
;

// 使用 GDXXRW 从 Excel 导入数据
$Call GDXXRW InputDataCoalUpdated.xlsx
    set=g rdim=1 rng=CoalPlantData!a4:a500                 // 定义发电厂数据集合。
    set=t cdim=1 rng=Price_Distribution!b3:k3             // 定义时间段集合。
    par=GenData  RDim=1 CDim=1 rng=CoalPlantData!a3:aa500 // 发电厂级别数据。
    par=FC_PPA  RDim=1 CDim=1 rng=FC_PPA!a5:aa500         // 容量支付数据。
    par=Price_Gen  RDim=1 CDim=1 rng=Price_Gen!a3:aa500   // 价格和煤炭发电预测。
    par=Price_Dist  RDim=1 CDim=1 rng=Price_Distribution!a3:K23  // 价格分布。
    par=Price_Dur  RDim=1 CDim=1 rng=Price_Distribution!N3:O13   // 价格区间持续时间。
    par=Other  RDim=1 CDim=1 rng=Other!a2:aa500           // 其他数据。
$GDXIN InputDataCoalUpdated.gdx
$LOAD g t GenData Price_gen Price_dist Price_dur Other FC_PPA
$GDXIN

display g, t, GenData, Price_gen, Price_dist, Price_dur, Other, FC_PPA;

// 折现率计算
Parameter DR(y) discount rate, life(g), cost(g,y), price_dist1(y,p,t), index(p), Flag(s), rev_unit(g,y,p);

DR(y) = 1/(1 + Other("DisCountRate", "Value"))**(ord(y)-1);  // 每年的折现率。

// 计算发电厂的寿命（年数）
life(g) = 2021 - GenData(g, "startyear");

// 基于发电厂寿命的成本增长
Cost(g,y)$(life(g)<10) = GenData(g, "cost") * (1 + Other("costesc_lessthan10", "value"))**(ord(y)-1);
Cost(g,y)$(life(g)>=10 and life(g)<=30) = GenData(g, "cost") * (1 + Other("costesc_10-30years", "value"))**(ord(y)-1);
Cost(g,y)$(life(g)>30) = GenData(g, "cost") * (1 + Other("costesc_30plus", "value"))**(ord(y)-1);

// 初始化价格分布
price_Dist1(y,"MarketPrice",t) = Price_Dist(y,t);
price_Dist1(y,"AvgPPAPrice",t) = 1;  // PPA 价格固定为 1。

// 情景和价格情景标记
index("AvgPPAPrice") = 1;
index("MarketPrice") = 0;
Flag("BAU") = 1;
Flag("AD") = 0;

// 收入计算
rev_unit(g,y,"MarketPrice") = GenData(g, "MarketPrice");
rev_unit(g,y,"AvgPPAPrice") = GenData(g, "FIXED COST") + Cost(g,y);

display life, cost;

// 定义变量
Variables
    Cap(g,y)         capacity in MW                 // 每年发电厂的容量（MW）
    Gen(g,y,t)       generation in MW               // 每年的发电量（MW）
    Retire(g,y)      retire decision (1 = retire)   // 退役决策变量
    Retired(g,y)     retired state (1 = retired)    // 退役状态变量
    TotNetRev        total net revenue for all coal plants  // 所有发电厂的总净收入
;

// 定义正变量和二进制变量
positive variables cap, gen;   // 定义容量和发电量为正变量
binary variables retire;       // 退役变量为二进制变量

// 约束定义
Equation
    maxcoalgen(y)  max coal generation to meet IEA forecasts  // 最大发电量约束，符合 IEA 预测
    obj            objective function                        // 目标函数
    minPLF(g,y)    minimum load factor (set to 25%)           // 最小负荷系数约束（设为 25%）
    maxPLF(g,y)    maximum load factor (set to 25%)           // 最大负荷系数约束（设为 25%）
    CapBal(g,y)    capacity balance allowing for retirement   // 容量平衡约束，允许退役
    CapBal1(g,y)   initial capacity balance                   // 初始容量平衡
    MaxRetire(g)   limit retirements to one per plant         // 限制每个发电厂最多退役一次
    MinCapacity(y) minimum capacity to match load factors     // 最小容量约束，以匹配负荷系数
;

// 最大发电量约束
MaxCoalGen(y).. 
    Sum((g,t), Gen(g,y,t) * Price_Dur(t, "PercentTime") * 8.76 / 1000) =e= 
    Sum(s$SetScenario(s), Price_Gen(y,s));

// 最小和最大负荷系数约束
MinPLF(g,y).. 
    Sum(t, Gen(g,y,t) * Price_Dur(t, "PercentTime") * 8.76 / 1000) =g=
    Cap(g,y) * 8.76 / 1000 * Other("minplf", "value");

MaxPLF(g,y).. 
    Sum(t, Gen(g,y,t) * Price_Dur(t, "PercentTime") * 8.76 / 1000) =l= 
    Cap(g,y) * 8.76 / 1000 * Other("maxplf", "value");

// 最大化净收入的目标函数
Obj..
    TotNetRev =e= Sum(y, DR(y) * (
        - Sum(p, GenData(g, "Capacity") * Flag(s) * FC_PPA(g,y) * Index(p)) +
        Sum((g), Sum(p$SetPriceScenario(p), Sum(t, (rev_unit(g,y,p) * Price_Dist1(y,p,t) - Cost(g,y)) * Gen(g,y,t) * Price_Dur(t, "PercentTime") * 8.76 / 1000)))
    ));

// 模型定义和求解
Model StrandedCost /all/;

Solve StrandedCost using MIP maximizing TotNetRev;

// 提取并总结结果
Parameter 
    totgen(y), 
    NetRev(g,*), 
    Retire_BAU(g,y), 
    Summary(y,*), 
    Mega_Summary(*,*);

totgen(y) = Sum(g, Sum(t, Gen.l(g,y,t) * Price_Dur(t, "PercentTime") * 8.76 / 1000));
NetRev(g,y) = Sum(p, Cap.l(g,y) * FC_PPA(g,y) * Index(p)) - Sum(p$SetPriceScenario(p), Sum(t, (rev_unit(g,y,p) - Cost(g,y)) * Gen.l(g,y,t)));

// 将结果导出到 Excel
EXECUTE_UNLOAD 'CoalSummary.gdx' 
    Summary, NetRev, Mega_Summary;

EXECUTE 'GDXXRW CoalSummary.gdx o=CoalAnalysisResults.xlsx';

display retire.l, gen.l, totnetrev.l, totgen, netrev, summary;
