# FFRM Python

This repository implements 

## Installation

1. Clone this repository:
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
3. Ensure a compatible solver (e.g., glpk, cbc, gurobi, or cplex) is installed.

## Usage

### Running the Model

1. Run the optimization model:
```bash
python solve_model.py --solver gurobi
```
2. The model will generate and export results (`CoalAnalysisResults_Scenarios.xlsx`) to the project directory.