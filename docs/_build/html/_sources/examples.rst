.. _examples:
 
===========
Examples
===========

Before you start
----------------

Before running any examples, make sure you have:

1. installed FFRM and its dependencies (see :doc:`install`), and
2. activated the Python environment you use for FFRM.

For example:

.. code-block:: bash

   (base) ~/ffrm_python$ conda activate ffrm
   (ffrm) ~/ffrm_python$

Example 1 – Run FFRM with the example Botswana input file
------------------------------------------------------------

**Goal:** Run FFRM once using the Botswana Excel input file, which consists of primarly a PPA regime. 
This will read plant-level data and prices from the workbook, solve the
model, and write summary outputs.

**Input file**

The repository includes an example FFRM input workbook for 
Botswana's fossil fuel plants.  

Examples
========

Below are some simple examples you can follow to understand how the
Fossil Fuel Retirement Model (FFRM) works.

.. note::

   In the grey boxes below, type each line into a terminal
   (or Anaconda Prompt on Windows) and press Enter. You do **not**
   need to type anything before the command itself.

Before you start
----------------

Before running any examples, make sure you have:

* installed FFRM and its dependencies (see :doc:`install`), and
* activated the Python environment you use for FFRM.

For example:

.. code-block:: console

   conda activate ffrm
   cd path/to/ffrm_python

Example 1 – Run FFRM with the example Philippines input file
------------------------------------------------------------

**Goal:** Run FFRM once using the bundled Philippines Excel input file.
This will read plant-level data and prices from the workbook, solve the
model, and write summary outputs.

Input file
~~~~~~~~~~

The repository includes an example FFRM input workbook for the
Philippines:

* :file:`docs/data/250810 FFRM Data Input File .xlsx`

This workbook contains:

* a **Plant Data** sheet with plant-level costs, capacities, start year,
  technology type and price regime
* an **FC_PPA** sheet with time-varying fixed costs for plants under PPAs
* a **Price_Gen** sheet with generation price assumptions
* other sheets used internally by FFRM

Steps
~~~~~

1. From the project root (:file:`ffrm_python`), run FFRM pointing to the
   example Excel file:

   .. code-block:: console

      python model.py --input-excel "docs/data/250810 FFRM Data Input File .xlsx"

   Replace the command above with the entry point you normally use to
   run FFRM (for example a different script name or flag), but keep the
   Excel path as shown.

2. When the run finishes, FFRM will create a results folder, for
   example:

   .. code-block:: text

      ffrm_python/
      ├── Summary.csv
      ├── results_YYYYMMDD_HHMMSS/
      │   ├── plant_results.csv
      │   ├── cashflows.csv
      │   ├── debt_and_equity.csv
      │   └── ...

   The exact filenames may differ, but you should see a time-stamped
   results folder and a :file:`Summary.csv` file.

3. Open :file:`Summary.csv` in your spreadsheet editor. This gives a
   high-level view of key FFRM outputs (for example, stranded asset
   values, lost FCFE, and unamortised debt).

4. (Optional) Use any dashboard or plotting scripts in the repository to
   generate figures from these outputs.

Example 2 – Change an assumption in the Excel file and re-run
-------------------------------------------------------------

**Goal:** Change one simple assumption in the Excel input file, re-run
FFRM, and see the impact on the results.

In this example we will change a coal plant’s variable cost and compare
the outputs.

Steps
~~~~~

1. Make a copy of the example workbook so you have an original and a
   modified version, for example:

   .. code-block:: console

      cp "docs/data/250810 FFRM Data Input File .xlsx" \
         "docs/data/FFRM_Philippines_higher_fuel_cost.xlsx"

2. Open :file:`docs/data/FFRM_Philippines_higher_fuel_cost.xlsx` in
   Excel or LibreOffice.

3. Go to the **Plant Data** sheet and adjust the
   ``Variable Cost ($/MWh)`` column for one or more plants (for example,
   increase coal plant fuel costs by 10–20%).

4. Save the workbook.

5. Run FFRM again, this time pointing to the modified workbook:

   .. code-block:: console

      python model.py --input-excel "docs/data/FFRM_Philippines_higher_fuel_cost.xlsx"

6. Compare the new results folder and :file:`Summary.csv` to the
   baseline run in Example 1. You should see changes in plant-level
   profitability, retirement timing, and total stranded asset values.

Example 3 – Create your own country case
----------------------------------------

**Goal:** Use the FFRM Excel template to create a new country case
(starting from the Philippines example), then run FFRM for that case.

High-level steps
~~~~~~~~~~~~~~~~

1. Copy the Philippines workbook to a new file and rename it, for
   example :file:`FFRM_MyCountry.xlsx`.

2. Update plant-level information in the **Plant Data** sheet (plant
   names, capacities, start years, technology types, price regimes).

3. Update PPA-related inputs in **FC_PPA** and price assumptions in
   **Price_Gen** to match your country.

4. Run FFRM with your new workbook:

   .. code-block:: console

      python model.py --input-excel "docs/data/FFRM_MyCountry.xlsx"

5. Inspect the new results folder and :file:`Summary.csv` and compare
   them to the Philippines example.

Next steps
----------

These examples are deliberately simple and focus on working with the
Excel input file and basic model runs. For more detail on how FFRM is
structured and how individual components (e.g. PPAs, regulated plants,
market-based plants) are modelled, see :doc:`structure`.















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
