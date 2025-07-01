# Welcome to the FFRM(Preview) Documentation

Fossil Fuel Retirement Model (FFRM) is an open-source python based fossil fuel retirement model. It was originally developed by the [World Bank](https://www.worldbank.org/ext/en/home) as a coal retirement optimisation model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.

The model utilises a Pyomo-based optimisation framework to endogenously calculate stranded cost taking into consideration commercial and market issues. It uses projections for capacity and production of fossil fuel power plants to explore their retirement profile under two types of price regimes, PPA and market price regime to assess at what capacity does fossil fuel power plants become stranded and explores how this influences total compensation for stranded plants.  
 
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
 
## Dependencies
FFRM relies on numerous open-source community supported tools. Below is a list of the heavily used packages.

[Python](https://www.python.org/): All data processing is written in the Python programming language

[GLPK](https://www.gnu.org/software/glpk/): Open-source linear programming toolkit

[CBC](https://github.com/coin-or/Cbc):Open-source linear program solver

## [Documentation](https://ffrm-python.readthedocs.io/en/latest/index.html)

## Key publications
Suski, A., Hong, L., and Chattopadhyay, D. (2022) 'Modeling coal plant stranded costs for decarbonization pathway analyses', Energy for Sustainable Development, 71, pp. 480-489. Available at: https://www.sciencedirect.com/science/article/pii/S0973082622002022 
