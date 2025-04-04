.. _examples:
 
===========
Examples
===========

Run with specific solver options
---------------------------------
Run the following command to specify solver options:

.. code-block:: bash
  
    python model.py --solver cplex --solver-options threads=4 timelimit=3600

Run multiple scenarios
-----------------------
Run the following command to specify multiple scenarios:

.. code-block:: bash
   
    python model.py --scenarios BAU AD --price-scenarios MarketPrice AvgPPAPrice

Specify custom input/output files
---------------------------------
Run the following command to specify custom input/output files:

.. code-block:: bash
   
    python model.py --input-file data/custom_input.xlsx --output-file results/output.xlsx

Input Data Format
-----------------
The input **Excel file** must contain the following sheets:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - **Sheet Name**
     - **Description**
   * - Generation Capacity
     - Capacity of powerplants  *(MW)* 
   * - Variable Costs
     - Operational, maintenance, and fuel costs  *(USD/MWh)* 
   * - Annual Fixed Costs
     - Annual fixed costs for the original PPA period only
   * - Market Price
     - Dual values (shadow prices) from models like OSeMOSYS if this information isn’t open source
   * - Commission Year
     - The start year when a plant connects to the grid and starts generating electricity
   * - Time blocks
     - Duration of the 10 time blocks, as a percentage of hours in the year, reflecting average Market Prices for each time block *(USD/MWh)*
   * - Generation targets
     - Annual generation targets for defined scenarios *(TWh)*

Output Format
-------------
The model generates an **Excel file** containing:

.. code-block:: text

    - Total generation by plant and year
    - Net revenue calculations
    - Capacity data
    - Retirement schedules

Error Handling
--------------
The model includes **comprehensive error handling** for:

.. code-block:: text

    - Missing input files
    - Invalid solver configurations
    - Scenario processing errors
    - Result saving issues
