.. _equations:
 
 
================= 
Structure of FFRM
=================  

The structure of the FFRM comprises eight core mathematical equations used to determine the foregone net revenue of fossil fuel fleets. This is analysed under two regimes: the **PPA** regime, which is based on commercially negotiated power purchase agreements or the **market-based** regime, which reflects projected hourly spot prices that are determined exogenously.

**Equation 1**
 
.. math::

   NR = \left\{
       \sum_{y,g,t,s,p} (P_{y,p,t} - Cost_{g,y}) \cdot Gen_{g,y,t,s,p}
       - \sum_{y,g,t,s,p} FC_{g,y} \cdot \left(Capacity_g - RetireC_{g,y,s,p}\right)
   \right.

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
