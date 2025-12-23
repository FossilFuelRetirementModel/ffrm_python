.. _examples:

========
Examples
========
 
Quickstart
----------

Make sure you have:

1. Installed FFRM and its dependencies (see :doc:`install`).
2. Activated the Python environment you use for FFRM.

.. code-block:: console

   conda activate ffrm
   cd path/to/ffrm_python


Example 1 — Run FFRM with the Botswana Example Workbook
-------------------------------------------------------

**Goal:** Run FFRM once using the bundled Botswana Excel input file. This is primarily a PPA regime.  

**Input file:**
* :file:`Examples/FFRM Data Input File.xlsx`
* Browse on GitHub: `Examples folder on GitHub <https://github.com/FossilFuelRetirementModel/ffrm_python/tree/main/Examples>`_.

**Steps:**

1. From the project root (:file:`ffrm_python`), run:

   .. code-block:: console

      python model.py --input-excel "Examples/FFRM Data Input File.xlsx"

2. When the run finishes, you should see outputs similar to:

   .. code-block:: text

      ffrm_python/
      ├── Summary.csv
      └── results_YYYYMMDD_HHMMSS/        (optional; depends on configuration)
          ├── plant_results.csv 
          └── ...

3. Open :file:`Summary.csv` in your spreadsheet editor to review high-level outputs.

.. note::

   Exact filenames can differ depending on your configuration and version of FFRM.


Example 2 — Change an assumption and Re-run
-------------------------------------------

**Goal:** Change one assumption in an Excel input file, re-run FFRM, and compare results.

**Steps:**

1. Make a copy of the workbook:

   .. code-block:: console

      cp "Examples/FFRM Data Input File.xlsx" \
         "Examples/FFRM_Botswana_higher_fuel_cost.xlsx"

2. Open :file:`Examples/FFRM_Botswana_higher_fuel_cost.xlsx` in Excel or LibreOffice.
3. In the :guilabel:`Plant Data` sheet, increase a plant’s variable cost by 10–20%.
4. Save the workbook.
5. Run FFRM again:

   .. code-block:: console

      python model.py --input-excel "Examples/FFRM_Botswana_higher_fuel_cost.xlsx"

6. Compare the new :file:`Summary.csv` (and any results folder outputs) to the baseline run.


Example 3 — Create your own country case
----------------------------------------

**Goal:** Create a new country workbook based on an existing example and run FFRM.

**Steps:**

1. Copy an example workbook and rename it (e.g. :file:`Examples/FFRM_MyCountry.xlsx`).
2. Update plant-level information in :guilabel:`Plant Data`:

   * plant names, capacities, start years
   * technology types and price regimes

3. Update regime-specific inputs (e.g. :guilabel:`FC_PPA`) and price assumptions
   (e.g. :guilabel:`Price_Gen`) to match your country.
4. Run FFRM:

   .. code-block:: console

      python model.py --input-excel "Examples/FFRM_MyCountry.xlsx"

5. Inspect :file:`Summary.csv` and compare it with the example outputs.


Reference
---------

**Common required sheets:**

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

.. tip::

   If you see errors like ``usecols ... out-of-bounds`` for :guilabel:`Plant Data`,
   it usually means the workbook layout (columns/headers) doesn’t match what your parser expects.

**Typical outputs:**

* :file:`Summary.csv` (high-level summary outputs)
* plant-level results (e.g. :file:`plant_results.csv`)
 


Next steps
----------

For more detail on how FFRM is structured and how components are modelled, see :doc:`structure`.
 