* Stranded asset compensation calculations

option optcr=0.06;

$inlinecom { }

Sets
g
y /2021*2040/
t timeblocks

s scenarios /BAU, AD/ {Business as usual and Accelerated Decarbonization}

p price scenarios /MarketPrice, AvgPPAPrice/



;



Parameter SetScenario(s) /BAU 1, AD 0/     {set BAU to 1 - the model runs AD after BAU automatically}
SetPriceScenario(p) /MarketPrice 1, AvgPPAPrice 0/ {set only one of them to 1}
;


Parameters GenData(g,*) plant level data, Price_gen(y,*) avg price and total coal gen forecast, Price_dist(y,t) distribution of prices as a multiple of avg price, Price_dur(t,*) duration of price blocks, Other(*,*) all other parameters
Parameter FC_PPA(g,y) mandatory capacity payment calculated at 85% PLF for 25 year period

$Call GDXXRW   InputDataCoalUpdated.xlsx  set=g rdim=1 rng=CoalPlantData!a4:a500 set=t cdim=1 rng=Price_Distribution!b3:k3 par=GenData  RDim=1 CDim=1 rng=CoalPlantData!a3:aa500 par=FC_PPA  RDim=1 CDim=1 rng=FC_PPA!a5:aa500 par=Price_Gen  RDim=1 CDim=1 rng=Price_Gen!a3:aa500 par=Price_Dist  RDim=1 CDim=1 rng=Price_Distribution!a3:K23 par=Price_Dur  RDim=1 CDim=1 rng=Price_Distribution!N3:O13 par=Other  RDim=1 CDim=1 rng=Other!a2:aa500
$GDXIN  InputDataCoalUpdated.gdx
$LOAD g t gendata price_gen price_dist price_dur other FC_PPA
$GDXIN

display g,t, gendata, price_gen, price_dist, price_dur, other, FC_PPA;



Parameter DR(y) discount rate, life(g), cost(g,y), price_dist1(y,p,t), index(p), Flag(s), rev_unit(g,y,p);


DR(y) = 1/(1+Other("DisCountRate","Value"))**(ord(y)-1);

life(g)=2021-gendata(g,"startyear") ;

Cost(g,y)$(life(g)<10)=GenData(g,"cost")*(1+other("costesc_lessthan10","value"))**(ord(y)-1) ;
Cost(g,y)$(life(g) ge 10 and life(g) le 30)=GenData(g,"cost")*(1+other("costesc_10-30years","value"))**(ord(y)-1) ;
Cost(g,y)$(life(g)>30)=GenData(g,"cost")*(1+other("costesc_30plus","value"))**(ord(y)-1) ;

price_Dist1(y,"MarketPrice",t) = Price_Dist(y,t) ;
price_Dist1(y,"AvgPPAPrice",t) = 1 ;
 index("AvgPPAPrice")=1;
index("MarketPrice")=0;
Flag("BAU")= 1;
Flag("AD")= 0;


rev_unit(g,y,"MarketPrice") = GenData(g,"MarketPrice")   ;
rev_unit(g,y,"AvgPPAPrice") = GenData(g,"FIXED COST") + Cost(g,y)  ;


display life, cost;


Variables

Cap(g,y)         capacity in MW
Gen(g,y,t)         generation in MW
Retire(g,y)      retire plant if its past its life or CF falls persistently below 25% for all subsequent years - set to 1 for the year when it is retired
Retired(g,y)     Retired state set to 1 for all years from the year it is retired

TotNetRev        total net revenue for all coal plants

;

positive variables cap, gen; binary variables retire;

$ontext
Version 2 - before June 11
Gen.fx(g,y,t)$((ord(y)+life(g)-1) > Other("maxlife","value")) = 0;

Cap.fx(g,y)$(ord(y)=1) = GenData(g,"capacity") ;

Gen.UP(g,y,t) = GenData(g,"capacity");
Retire.fx(g,y)$(ord(y)=1 and  ((ord(y)+life(g)-1) lt Other("maxlife","value")) )=0;

$offtext

Gen.fx(g,y,t)$((ord(y)+life(g)-1) > Other("maxlife","value")) = 0;

*Cap.fx(g,y)$(ord(y)=1) = GenData(g,"capacity") ;

Gen.UP(g,y,t) = GenData(g,"capacity");
*Retire.fx(g,y)$(ord(y)=1 and  ((ord(y)+life(g)-1) lt Other("maxlife","value")) )=0;

Cap.fx(g,y)$( (ord(y)+life(g)-1) > Other("maxlife","value")) = 0;

Gen.fx(g,y,t)$((ord(y)+life(g)-1) > Other("maxlife","value")) = 0;


Equation

maxcoalgen(y)  max TWh to be delivered as per IEA forecast
obj            objective function
minPLF(g,y)    below which the plant must be retired - set at 25%
maxPLF(g,y)    below which the plant must be retired - set at 25%
CapBal(g,y)    capacity balance allowing for retirement
CapBal1(g,y)
MaxRetire(g)
MinCapacity(y)  minimum capacity associated with GWh to match load factor of 0.66

;


MaxCoalGen(y).. Sum((g,t), Gen(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000) =e= Sum(s$SetScenario(s), Price_Gen(y,s)) ;

MinPLF(g,y).. Sum(t,Gen(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000) =g= Cap(g,y)*8.76/1000*Other("minplf","value");

MaxPLF(g,y).. Sum(t,Gen(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000) =l= Cap(g,y)*8.76/1000*Other("maxplf","value");

MaxRetire(g).. Sum(y, Retire(g,y)) =l= 1;

CapBal(g,y)$(ord(y)>1).. Cap(g,y) =e= Cap(g,y-1) - Retire(g,y)*GenData(g,"Capacity") ;

CapBal1(g,y)$(ord(y)=1).. Cap(g,y) =e= GenData(g,"Capacity") - Retire(g,y)*GenData(g,"Capacity") ;

MinCapacity(y).. Sum(g, Cap(g,y)) =g= Sum(s$SetScenario(s), Price_Gen(y,s))*1000000/(8760*0.75) ;

Obj.. TotNetRev =e= Sum(y, DR(y)*( - Sum(p, Sum(g,Sum(s$SetScenario(s),(GenData(g,"Capacity")*Flag(s)+Cap(g,y)*(1-Flag(s))))*(FC_PPA(g,y)*Index(p)+100*(1-index(p)))))/1e6 + Sum((g), Sum(p$SetPriceScenario(p), Sum(t,(rev_unit(g,y,p)*Price_Dist1(y,p,t) - Cost(g,y))*Gen(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000))))) ;


Model StrandedCost /all/ ;

StrandedCost.optfile=1;

*FC_PPA(g,y)=0; {just to test what happens if the fixed costs are set to zero}

Solve StrandedCost using MIP maximizing TotNetRev;



parameter totgen(y), NetRev(g,*), Retire_BAU(g,y), Capacity_BAU(g,y), Summary(y,*), PlantGen(g,*);

totgen(y) = Sum(g, Sum(t,Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000)) ;

NetRev(g,y) =  {- Sum(p,GenData(g,"Capacity")*(FC_PPA(g,y)*Index(p)+100*(1-index(p))))/1e6} + Sum(p$SetPriceScenario(p), Sum(t,(rev_unit(g,y,p)*Price_Dist1(y,p,t) - Cost(g,y))*Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000))  ;
NetRev(g,"Depreciated Capex $m")= Max(GenData(g,"Capacity")*Other("CoalCapex","Value")*(1-Other("SLD","Value")*Life(g)),0)/1000;


PlantGen(g,y) = Sum(t,Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76) ;


PlantGen(g,"Life") = Life(g) ;

Summary(y,"Total Capacity GW") = Sum(g, Cap.l(g,y))/1000 ;

Summary(y,"Total Coal Gen TWh") = TotGen(y) ;

Summary(y,"Total Undiscounted Net Revenue $b") = Sum(g, NetRev(g,y))/1000 ;

Retire_BAU(g,y)=Retire.l(g,y);

Capacity_BAU(g,y)=Cap.l(g,y);



SetScenario("AD")=1;
SetScenario("BAU")=0;


Solve StrandedCost using MIP maximizing TotNetRev;

parameter totgen_AD(y), NetRev_AD(g,*), Capacity_AD(g,y), Retire_AD(g,y), Summary_AD(y,*), PlantGen_AD(g,*);

totgen_AD(y) = Sum(g, Sum(t,Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000)) ;

Retire_AD(g,y)=Retire.l(g,y);

Capacity_AD(g,y)=Cap.l(g,y);

NetRev_AD(g,y) =  {- Sum(p,Cap.l(g,y)*(FC_PPA(g,y)*Index(p)+100*(1-index(p))))/1e6} + Sum(p$SetPriceScenario(p), Sum(t,(rev_unit(g,y,p)*Price_Dist1(y,p,t) - Cost(g,y))*Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76/1000))  ;
NetRev(g,"Depreciated Capex $m")= Max(GenData(g,"Capacity")*Other("CoalCapex","Value")*(1-Other("SLD","Value")*Life(g)),0)/1000;


PlantGen_AD(g,y) = Sum(t,Gen.l(g,y,t)*Price_Dur(t,"PercentTime")*8.76) ;


PlantGen_AD(g,"Life") = Life(g) ;

Summary_AD(y,"Total Capacity GW") = Sum(g, Cap.l(g,y))/1000 ;

Summary_AD(y,"Total Coal Gen TWh") = TotGen_AD(y) ;

Summary_AD(y,"Total Undiscounted Net Revenue $b") = Sum(g, NetRev_AD(g,y))/1000 ;


Parameter NetRevDiff(g,y);

NetRevDiff(g,y) = NetRev(g,y) - NetRev_AD(g,y);	§

Parameter Mega_Summary(*,*), SummaryNetRevDiff(g,*), SummaryNetRevDiff1(g,*), Ratio(g) ;

Mega_Summary("Capacity by 2040","BAU") = Summary("2040","Total Capacity GW") ;
Mega_Summary("Capacity by 2040","AD") = Summary_AD("2040","Total Capacity GW") ;
Mega_Summary("Coal TWh by 2040","BAU") = Summary("2040","Total Coal Gen TWh") ;
Mega_Summary("Coal TWh by 2040","AD") = Summary_AD("2040","Total Coal Gen TWh") ;
Mega_Summary("Coal TWh by 2040","BAU") = Summary("2040","Total Coal Gen TWh") ;
Mega_Summary("Discounted Net Revenue $b","BAU") = Sum(y, DR(y)*Summary(y,"Total Undiscounted Net Revenue $b")) ;
Mega_Summary("Discounted Net Revenue $b","AD") = Sum(y, DR(y)*Summary_AD(y,"Total Undiscounted Net Revenue $b")) ;

SummaryNetRevDiff1(g,"BAU") = Sum(y, DR(y)*NetRev(g,y)) ;
SummaryNetRevDiff1(g,"AD") = Sum(y, DR(y)*NetRev_AD(g,y)) ;

Ratio(g)$SummaryNetRevDiff1(g,"BAU") = SummaryNetRevDiff1(g,"AD")/SummaryNetRevDiff1(g,"BAU")    ;

set gg(g);

gg(g)$(ratio(g)<0.9)=yes ;

SummaryNetRevDiff(gg,"BAU")$(Ratio(gg) < 0.9) = Sum(y, DR(y)*NetRev(gg,y)) ;
SummaryNetRevDiff(gg,"AD")$(Ratio(gg) < 0.9) = Sum(y, DR(y)*NetRev_AD(gg,y)) ;


display ratio, gg;



EXECUTE_UNLOAD 'CoalSummary', Summary, NetRev, Summary_AD, NetRev_AD, NetRevDiff, Retire_BAU, Retire_AD, PlantGen, PlantGen_AD, Capacity_BAU, Capacity_AD, Mega_Summary, SummaryNetRevDiff;
EXECUTE 'GDXXRW CoalSummary.gdx  par=Retire_BAU rng=Retirement_Sched_BAU!A4 par=Retire_AD rng=Retirement_Sched_AD!A4 par=Capacity_BAU rng=Capacity_BAU!A4 par=Capacity_AD rng=Capacity_AD!A4 par=PlantGen rng=Plant_GWh!A4 par=PlantGen_AD rng=Plant_GWh_AD!A4 par=NetRev rng=Plant_Summary!A4 par=Summary rng=Summary!A4 par=NetRev_AD rng=Plant_Summary_AD!A4 par=Summary_AD rng=Summary_AD!A4 par=Mega_Summary rng=Mega_Summary!A4 par=SummaryNetRevDiff rng=NetRev_Diff!A4 o=CoalAnalysisResults.xlsx';


display retire.l, gen.l, totnetrev.l, totgen, netrev, summary;






