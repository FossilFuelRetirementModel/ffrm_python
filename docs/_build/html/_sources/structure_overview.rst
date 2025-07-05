Structure Overview
==================
 

The mathematical structure of FFRM is formulated to maximise a fossil fuel powerplant revenue in order to meet a target generation under a number of regimes. It consists of a series of sets, parameters and equations used in the optimisation process.

- A core element of the model is to consider both a reference (business-as-usual) and a decarbonisation generation trajectory under these various regimes.
- A functionality of the model is to also limit the level of asset stranding. So if a powerplant's net revenue falls below a certain level or a plant load factor (a measure of how much the plant is being utilised), then plant cannot be in operation.

The structure of the FFRM comprises eight core mathematical equations used to determine the foregone net revenue of fossil fuel fleets. This is analysed under two regimes: the **PPA** regime, which is based on commercially negotiated power purchase agreements or the **market-based** regime, which reflects projected hourly spot prices that are determined exogenously.

**Equation 1**

The equation is calculating fleetwide net revenue either for the market regime (projected hourly spot prices are exogenously inputted into the model) or a commercial power purchasing agreement.

- The first part of the equation represents the revenue subtracted by variable cost. This is where electricity price at year **(y)**, price **(p)** and time **(t)** is subtracted from variable cost of the generator in year **(y)**. Then this is then multiplied by electricity generated.
- The second part of the equation represents fixed cost multiped by retired capacity. This total is subtracted from the first part of the equation.         

Therefore the difference in the **systemwide net revenue** between the business-as-usual scenario and the decarbonisation scenario would be used to calculate the **foregone revenue**. Retired capacity can use the foregone revenue as a calculation of **stranded cost**.  

.. code-block:: ampl

    NR = sum {y, g, t, s, p} (P[y,p,t] - Cost[g,y]) * Gen[g,y,t,s,p]
         - sum {y, g, t, s, p} FC[g,y] * (Capacity[g] - RetireC[g,y,s,p]);

**Equation 2**

.. code-block:: ampl

    (NR_prime[g,s_prime,p_prime] - NR[g,s,p]) / NR_prime[g,s_prime,p_prime] <= alpha

**Equation 3**

.. code-block:: ampl

    sum {t, g} Gen[g,y,t,s,p] * H[t] = Target[y,s,p]

**Equation 4**

.. code-block:: ampl

    sum {t} Gen[g,y,t,s,p] * H[t] >= MinGen[g]

**Equation 5**

.. code-block:: ampl

    sum {t} Gen[g,y,t,s,p] * H[t] <= MaxGen[g]

**Equation 6**

.. code-block:: ampl

    Cap[g,y,s,p] = Cap[g,y-1,s,p] - Retire[g,y,s,p] * Capacity[g]

**Equation 7**

.. code-block:: ampl

    sum {g} Cap[g,y,s,p] >= Target[y,s,p] / Phi[s,p]

**Equation 8**

.. code-block:: ampl

    RetireC[g,y,s,p] = sum {y_prime in Years: y_prime <= y} Retire[g,y_prime,s,p]
