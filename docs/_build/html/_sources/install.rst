.. _install:
===============
Getting Started
===============

.. _ignore:
Clone this repository
^^^^^^^^^^^^^^^^^^^^^

1. Go to the repository page on GitHub.
2. Click the green "Code" button.
3. Copy the repository URL.

To clone the repository and navigate into it, run:

.. code-block:: bash

   git clone [https://github.com/FossilFuelRetirementModel/ffrm_python.git]
   cd [ffrm_python]

.. _ignore:
Create and activate the FFRM Python environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On **Linux/Mac**, use:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate

On **Windows**, use:

.. code-block:: bash

   python -m venv venv
   venv\Scripts\activate

.. _ignore:
Install required packages
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install -r requirements.txt

.. _ignore:
Optional Solver Installation
----------------------------

Choose at least one of the following solvers:

.. _ignore:
Gurobi (Recommended)
^^^^^^^^^^^^^^^^^^^^^

1. Download from `Gurobi website <https://www.gurobi.com/downloads/>`_.
2. Get a license (free academic license available).
3. Follow the Gurobi installation guide.

.. _ignore:
GLPK (Free Alternative)
^^^^^^^^^^^^^^^^^^^^^^^

**Linux**:

.. code-block:: bash

   sudo apt-get install glpk-utils

**Mac**:

.. code-block:: bash

   brew install glpk

**Windows**:  
Download the binary from `GLPK website <https://www.gnu.org/software/glpk/>`_.

.. _ignore:
Usage
-----

.. _ignore:
Basic Usage
^^^^^^^^^^^

Run the model with default settings:

.. code-block:: bash

   python model.py

.. _ignore:
Advanced Usage
^^^^^^^^^^^^^^

The script supports various command-line arguments:

.. code-block:: bash

   python model.py --solver gurobi \
                   --scenarios BAU AD \
                   --price-scenarios MarketPrice AvgPPAPrice \
                   --input-file custom_input.xlsx \
                   --output-file results.xlsx

.. _ignore:
Command Line Arguments
^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Command Line Arguments
   :widths: 25 75
   :header-rows: 1

   * - Argument
     - Description
   * - ``--solver``
     - Selects the solver *(default: 'gurobi')*  
   * - *Options:*
     - ``'glpk'``, ``'cplex'``, ``'gurobi'``, ``'cbc'``  
   * - ``--solver-options``
     - Specify solver-specific options in ``key=value`` format  
   * - ``--scenarios``
     - Choose scenarios to run *(default: ["BAU"])*  
   * - *Options:*
     - ``"BAU"``, ``"AD"``  
   * - ``--price-scenarios``
     - Select price scenarios *(default: ["MarketPrice"])*  
   * - *Options:*
     - ``"MarketPrice"``, ``"AvgPPAPrice"``  
   * - ``--input-file``
     - Specify the **input Excel file path**  
   * - ``--output-file``
     - Specify the **output Excel file path**
