# Welcome to the FFRM Documentation

Fossil Fuel Retirement Model (FFRM) is an open-source python based fossil fuel retirement model. It was originally developed by the World Bank as a coal retirement optimisation model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.

The model utilises a Pyomo-based optimisation framework to endogenously calculate stranded cost taking into consideration commercial and market issues. It uses projections for capacity and production of fossil fuel power plants to explore their retirement profile under two types of price regimes, PPA and market price grime to assess at what capacity does fossil fuel power plants become stranded and explores how this influences total compensation for stranded plants. 

The model is designed to complement more detailed long-term capacity expansion models, such as OSeMOSYS, but can also be used as a standalone retirement model.  

## Background
A model developed by the World Bank, whereby it endogenously calculates stranded assets taking into consideration commercial and market issues.

## Aims
● The model is currently run for two different decarbonisation scenarios. These scenarios provide the basis for the foregone revenue calculation.
● The difference between the base level and the decarbonisation, specifically the lost profits from decarbonisatio

## Features

- Multi-scenario analysis (BAU, AD)
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
- **Plant data**
- **Time blocks**
- **Price scenarios**
- *[Add other required sheets]*

## **Output Format**
The model generates an **Excel file** containing:
- **Total generation** by plant and year
- **Net revenue calculations**
- **Capacity data**
- **Retirement schedules**

## **Error Handling**
The model includes **comprehensive error handling** for:
- **Missing input files**
- **Invalid solver configurations**
- **Scenario processing errors**
- **Result saving issues**

## Contributing

[contribution guidelines]

## Contact

## Acknowledgments
