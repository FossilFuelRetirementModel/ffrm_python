# Welcome to the FFRM(Preview) Documentation

Fossil Fuel Retirement Model (FFRM) is an open-source python based fossil fuel retirement model. It was originally developed by the [World Bank](https://www.worldbank.org/ext/en/home) as a coal retirement optimisation model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.

The model utilises a Pyomo-based optimisation framework to endogenously calculate stranded cost taking into consideration commercial and market issues. It uses projections for capacity and production of fossil fuel power plants to explore their retirement profile under two types of price regimes, PPA and market price regime to assess at what capacity does fossil fuel power plants become stranded and explores how this influences total compensation for stranded plants. 

The model is designed to complement more detailed long-term capacity expansion models, such as [OSeMOSYS](http://www.osemosys.org)
, but can also be used as a standalone retirement model.  

## Background
A model was developed by the [World Bank](https://www.worldbank.org/ext/en/home) to assess stranded cost under various defined scenarios. The model defines stranded cost as the difference in  plant revenue. In particular, the foregone revenue of plants that reach the end of their economic life in the decarbonisation scenarios, relative to the baseline scenario.
 
## Aims
The objective function of the model is set as maximisation of the net revenue at the fossil fuel power plants fleet, based on either: 
- Financial analysis of Power Purchase Agreements (PPAs),  where these are in place with known contractual terms 
- Or economic optimization of the market price, where marginal costs derived from a least-cost planning are  

The difference in net revenue between the BAU and a decarbonization scenario is used as a measure of foregone revenue.
 
## Features

- Multi-scenario analysis (Business As Usual, Accelerated Decarbonisation)
- Multiple price scenario support (Market Price, Average PPA Price)
- Flexible solver options (Gurobi, CPLEX, GLPK, CBC)
- Comprehensive result processing and Excel output
- Command-line interface for easy configuration

## Prerequisites

- Python 3.8 or higher
- A compatible solver (one of the following):
  - Gurobi (recommended)
  - CPLEX
  - GLPK
  - CBC

## Installation

1. Clone this repository:
   - Go to the repository page on GitHub.
   - Click the green "Code" button.
   - Copy the "repository-url".
```bash
git clone [repository-url]
cd [repository-name]
```
2. Create and activate a virtual environment:
```bash
# On Linux/Mac, use terminal:
python -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Optional Solver Installation
Choose at least one of the following solvers:

### Gurobi (Recommended)
1. Download from [Gurobi website](https://www.gurobi.com/downloads/)
2. Get a license (free academic license available)
3. Follow Gurobi installation guide

### GLPK (Free Alternative)
- Linux
```bash
# Linux
sudo apt-get install glpk-utils
```
- Mac
```bash
# Mac
brew install glpk
```

- Windows
Download binary from [GLPK website](https://www.gnu.org/software/glpk/)


## **Usage**

### **Basic Usage**
Run the model with default settings:
   ```bash
   python model.py
   ```

### **Advanced Usage**
The script supports various command-line arguments:

   ```bash
   python model.py --solver gurobi \
                   --scenarios BAU AD \
                   --price-scenarios MarketPrice AvgPPAPrice \
                   --input-file custom_input.xlsx \
                   --output-file results.xlsx
   ```

### **Command Line Arguments**
| Argument            | Description |
|---------------------|-------------|
| `--solver` | Selects the solver *(default: 'gurobi')*  |
| *Options:* | `'glpk'`, `'cplex'`, `'gurobi'`, `'cbc'`  |
| `--solver-options` | Specify solver-specific options in `key=value` format  |
| `--scenarios` | Choose scenarios to run *(default: ["BAU"])*  |
| *Options:* | `"BAU"`, `"AD"`  |
| `--price-scenarios` | Select price scenarios *(default: ["MarketPrice"])*  |
| *Options:* | `"MarketPrice"`, `"AvgPPAPrice"`  |
| `--input-file` | Specify the **input Excel file path** |
| `--output-file` | Specify the **output Excel file path** |

### **Examples**
7. **Run with specific solver options:**
   ```bash
   python model.py --solver cplex --solver-options threads=4 timelimit=3600
   ```
8. **Run multiple scenarios:**
   ```bash
   python model.py --scenarios BAU AD --price-scenarios MarketPrice AvgPPAPrice
   ```
9. **Specify custom input/output files:**
   ```bash
   python model.py --input-file data/custom_input.xlsx --output-file results/output.xlsx
   ```

## **Input Data Format**
The input **Excel file** must contain the following sheets:
 
 | Plant Input Data           | Description |
|---------------------|-------------|
| `Generation Capacity` | Capacity of powerplants *(MW)*  |
| `Variable Costs`| This consists of operational, maintenance, and fuel costs  *(USD/MWh)*  |
| `Annual Fixed Costs` | This details annual fixed costs for the original PPA period only  |
| `Market Price` | Dual Values (shadow prices) from models such as OSeMOSYS if this information isn’t available open source  |
| `Commission Year ` | The start year of a power plant; the year when the plant is connected to the grid and starts generating electricity  | 
| `Time blocks ` | Duration of the 10 time-blocks as percentage of hours in the year, reflecting average Market Prices for each of the time-blocks based on the model period *(USD/MWh)* |  
| `Generation targets` | Annual generation targets for defined scenario *(TWh)*|  
 
## **Output Format**
The model generates an **Excel file** containing:
- Total generation by plant and year
- Net revenue calculations
- Capacity data
- Retirement schedules

## **Error Handling**
The model includes **comprehensive error handling** for:
- **Missing input files**
- **Invalid solver configurations**
- **Scenario processing errors**
- **Result saving issues**

## Contributing to FFRM
We are very grateful that you are looking into how you can contribute to FFRM.

Contributing to FFRM is open to everyone who is interested, and we adopt an inclusive and open policy which is described in our code of conduct. If you have general questions or comments on the project, please submit them to our community discussion board or our Discord forum is a great place to ask general FFRM questions.

If you are experiencing issues please submit a new issue. 
 
## Change Log
Version 1.0
Initial release version 
 
## Dependencies
FFRM relies on numerous open-source community supported tools. Below is a list of the heavily used packages.

[Python](https://www.python.org/): All data processing is written in the Python programming language

[GLPK](https://www.gnu.org/software/glpk/): Open-source linear programming toolkit

[CBC](https://github.com/coin-or/Cbc):Open-source linear program solver

## Key publications
Suski, A., Hong, L., and Chattopadhyay, D. (2022) 'Modeling coal plant stranded costs for decarbonization pathway analyses', Energy for Sustainable Development, 71, pp. 480-489. Available at: https://www.sciencedirect.com/science/article/pii/S0973082622002022 
