.. _install:
===============
Getting Started
===============

Installation
------------

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
