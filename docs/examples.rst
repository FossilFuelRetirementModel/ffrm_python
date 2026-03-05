.. _examples:

========
Examples
========

Downloading FFRM
----------------

Make sure you have:

1. Installed FFRM and its dependencies (see :doc:`install`).
2. Activated the Python environment you use for FFRM.

.. code-block:: console

   conda activate ffrm
   cd path/to/ffrm_python


Navigating the FFRM input file
------------------------------

FFRM is driven by a six-tab Excel input workbook. Users calibrate these inputs before running the Python model.

An example input workbook is available on GitHub:
`FFRM Data Input File.xlsx <https://github.com/FossilFuelRetirementModel/ffrm_python/blob/new-input-format/Examples/FFRM%20Data%20Input%20File.xlsx>`_.

The Excel input file consists of six tabs:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Tab
     - Description
   * - Definitions
     - Overview of key definitions and a brief model description. This tab also defines the **technologies**
       and **scenarios** used in the analysis.
   * - Other
     - Technology-level parameters used across fossil fuel technologies, typically in three groups:
       (1) **Financing assumptions** (e.g., interest rate, loan term, discount rate),
       (2) **Cost and escalation assumptions** (e.g., CAPEX in $/kW, escalation rates by asset age),
       (3) **Operational constraints** (e.g., minimum/maximum plant load factor, maximum technical lifespan).
   * - Plant Data
     - Plant-level inputs such as capacity (MW), start year, and costs. Depending on the selected regime, this tab
       also includes the relevant price inputs (e.g., PPA prices and/or market prices).
   * - FC_PPA
     - Inputs for the **PPA regime**: fixed-cost component under PPAs, expressed as **$/MW/year**, typically
       calculated at **85% plant load factor**.
   * - Price_Gen
     - Projected electricity generation limits/targets applied to each fossil fuel technology (used to constrain
       generation trajectories under each scenario).
   * - Price_Distribution
     - Inputs for the **market regime**: the annual electricity price is distributed across representative
       hour-types (e.g., peak, shoulder, off-peak) to reflect intra-year price variation.


Example — Philippines case study
--------------------------------

.. note::

   This example uses the Philippines as a case study with a proxy dataset compiled from publicly available sources.
   Because data transparency can be limited in EMDEs, inputs and assumptions are simplified for learning purposes and results
   should be treated as illustrative.

To begin, identify which pricing regime(s) apply in your country.

**Hands-on task:** Go to the :ref:`Electricity Market Structure Map <electricity-market-structure-map>` on the
:doc:`home page <index>`, then search for ``Philippines``. To assist with this process, a pre-calibrated Philippines input workbook is available
`here <https://github.com/FossilFuelRetirementModel/ffrm_python/blob/new-input-format/Examples/FFRM%20Data%20Input%20File.xlsx>`_. Once you have downloaded the input workbook, run FFRM from the project root with the following command:
 
 
.. code-block:: console

   python model.py  

The time to build and solve the model will vary depending on your computer, but in general, this example will finish within minutes. Navigate to the newly created results/ folder. All available automatically generated results are summarized below.

Outputs created
^^^^^^^^^^^^^^^

When the run finishes, you should see outputs similar to:
 
.. code-block:: text

   results_YYYYYMMDD/
   ├── AD_20_AvgPPAPrice.lp
   ├── AD_20_AvgPPAPrice_PWRCOA001_results.xlsx
   ├── AD_20_AvgPPAPrice_PWRNGS001_results.xlsx
   ├── AD_20_AvgPPAPrice_PWRNGS002_results.xlsx
   ├── AD_20_AvgPPAPrice_PWROHC001_results.xlsx
   ├── AD_20_AvgPPAPrice_PWROHC002_results.xlsx
   ├── AD_20_AvgPPAPrice_PWROHC003_results.xlsx
   ├── AD_20_AvgPPAPrice_results.xlsx
   ├── AD_20_MarketPrice.lp
   ├── AD_20_MarketPrice_PWRCOA001_results.xlsx
   ├── AD_20_MarketPrice_PWRNGS001_results.xlsx
   ├── AD_20_MarketPrice_PWRNGS002_results.xlsx
   ├── AD_20_MarketPrice_PWROHC001_results.xlsx
   ├── AD_20_MarketPrice_PWROHC002_results.xlsx
   ├── AD_20_MarketPrice_PWROHC003_results.xlsx
   ├── AD_20_MarketPrice_results.xlsx
   ├── BAU_AvgPPAPrice.lp
   ├── BAU_AvgPPAPrice_PWRCOA001_results.xlsx
   ├── BAU_AvgPPAPrice_PWRNGS001_results.xlsx
   ├── BAU_AvgPPAPrice_PWRNGS002_results.xlsx
   ├── BAU_AvgPPAPrice_PWROHC001_results.xlsx
   ├── BAU_AvgPPAPrice_PWROHC002_results.xlsx
   ├── BAU_AvgPPAPrice_PWROHC003_results.xlsx
   ├── BAU_AvgPPAPrice_results.xlsx
   ├── BAU_MarketPrice.lp
   ├── BAU_MarketPrice_PWRCOA001_results.xlsx
   ├── BAU_MarketPrice_PWRNGS001_results.xlsx
   ├── BAU_MarketPrice_PWRNGS002_results.xlsx
   ├── BAU_MarketPrice_PWROHC001_results.xlsx
   ├── BAU_MarketPrice_PWROHC002_results.xlsx
   ├── BAU_MarketPrice_PWROHC003_results.xlsx
   ├── BAU_MarketPrice_results.xlsx
   ├── Results.xlsx
   └── data_loading.log

Each ``*_results.xlsx`` workbook contains a consistent set of sheets (e.g., ``AnnualSummary``, ``PlantGen``, ``plant_cap``,
``retire_sched``, ``TechGen``, ``TechCap``) that can be used for analysis and plotting.
 
.. note::

   Results files are named using the pattern ``Scenario_PriceScenario[_Technology]_results.xlsx``.
   For example, ``BAU_MarketPrice_results.xlsx`` contains the main outputs for the BAU + MarketPrice run, while
   ``BAU_MarketPrice_PWRCOA001_results.xlsx`` contains outputs for the coal technology in that same run. 

Next steps
----------

For more detail on how FFRM is structured and how components are modelled, see :doc:`structure`. 