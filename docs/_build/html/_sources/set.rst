.. _equations:
 
 
================= 
 Nomenclature
=================  

============

Sets
----

t
    Hours/sub-hours of the day
y
    Years
g
    Powerplant units
s
    Scenarios (BAU or Decarbonization)
p
    Price scenarios (market price or PPA)

Parameters
----------

α
    Net revenue minimum threshold to be maintained
MinGen_g
    Minimum plant load factor below which plant must be shut down
MaxGen_g
    Maximum plant load factor
Capacity_g
    Capacity of specified fossil fuel powerplant unit g
Cost_{g, y}
    Variable cost of unit g in year y
FC_{g, y}
    Fixed cost of unit in year y
θ_y
    Discount rate applied to cost parameters and net revenues
P_{y, p, t}
    Hourly price forecast for scenario p
H_t
    Number of hours in block t
Target_{y, s}
    Target specified fossil fuel powerplant generation in year y
Φ_{y, s, p}
    Minimum load factor

Variables
---------

NR
    Total system net revenue – objective function
NR_{g, s, p}
    Net revenue for scenarios (s, p) for specified fossil fuel powerplant unit g
Gen_{g, y, t, s, p}
    Generation from specified fossil fuel powerplant unit g
RetireC_{g, y, s, p}
    Retirement (cumulative) of specified fossil fuel powerplant unit g
Cap_{g, y, s, p}
    Remaining capacity of specified fossil fuel powerplant unit g
Retire_{g, y, s, p}
    Retirement of specified fossil fuel powerplant unit g {0, 1}
