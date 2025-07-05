.. _equations:
 
 
================= 
Equations
=================  

The mathematical structure of FFRM is formulated to maximise a fossil fuel powerplant revenue in order to meet a target generation under a number of regimes. It consists of a series of sets, parameters and equations used in the optimisation process.  
A core element of the model is to consider both a reference (business-as-usual) and a decarbonisation generation trajectory under these various regimes. A functionality of the model is to also limit the level of asset stranding. So if a powerplant's net revenue falls below a certain level or a plant load factor (a   measure of how much the plant is being utilised), then plant cannot be in operation. 

The structure of the FFRM comprises eight core mathematical equations used to determine the foregone net revenue of fossil fuel fleets. This is analysed under two regimes: the **PPA** regime, which is based on commercially negotiated power purchase agreements or the **market-based** regime, which reflects projected hourly spot prices that are determined exogenously.
 
**Equation 1**
 
.. math::

   NR = \left\{
       \sum_{y,g,t,s,p} (P_{y,p,t} - Cost_{g,y}) \cdot Gen_{g,y,t,s,p}
       - \sum_{y,g,t,s,p} FC_{g,y} \cdot \left(Capacity_g - RetireC_{g,y,s,p}\right)
   \right.

   .. code-block:: ampl

    NR = sum {y, g, t, s, p} (P[y,p,t] - Cost[g,y]) * Gen[g,y,t,s,p]
         - sum {y, g, t, s, p} FC[g,y] * (Capacity[g] - RetireC[g,y,s,p]);


**Equation 2** 

.. math::

   \frac{NR'_{g,s',p'} - NR_{g,s,p}}{NR'_{g,s',p'}} \leq \alpha

**Equation 3**

.. math::

   \sum_t \sum_g Gen_{g,y,t,s,p} \cdot H_t = Target_{y,s,p}

**Equation 4**

.. math::

   \sum_t Gen_{g,y,t,s,p} \cdot H_t \geq MinGen_g

**Equation 5**

.. math::

   \sum_t Gen_{g,y,t,s,p} \cdot H_t \leq MaxGen_g

**Equation 6**

.. math::

   Cap_{g,y,s,p} = Cap_{g,y-1,s,p} - Retire_{g,y,s,p} \cdot Capacity_g
