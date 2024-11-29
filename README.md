# Fossil Fuel Retirement Model

This repository implements a Pyomo-based optimization model for analyzing coal power plant operations, considering various scenarios and price conditions ........

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
```bash
git clone [repository-url]
cd [repository-name]
```

2. Create and activate a virtual environment:
```bash
# On Linux/Mac:
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
Choose one of the following solvers:

### Gurobi (Recommended)
1. Download from [Gurobi website](https://www.gurobi.com/downloads/)
2. Get a license (free academic license available)
3. Follow Gurobi installation guide

### GLPK (Free Alternative)
```bash
# Linux
sudo apt-get install glpk-utils

# Mac
brew install glpk

# Windows
# Download binary from GLPK website
```

## Usage

### Basic Usage

Run the model with default settings:
```bash
python model.py
```

### Advanced Usage

The script supports various command-line arguments:

```bash
python model.py --solver gurobi \
                --scenarios BAU AD \
                --price-scenarios MarketPrice AvgPPAPrice \
                --input-file custom_input.xlsx \
                --output-file results.xlsx
```

### Command Line Arguments

- `--solver`: Choose solver (default: 'gurobi')
  - Options: 'glpk', 'cplex', 'gurobi', 'cbc'
- `--solver-options`: Specify solver-specific options
  - Format: key=value pairs
- `--scenarios`: Choose scenarios to run (default: ["BAU"])
  - Options: "BAU", "AD"
- `--price-scenarios`: Choose price scenarios (default: ["MarketPrice"])
  - Options: "MarketPrice", "AvgPPAPrice"
- `--input-file`: Specify input Excel file path
- `--output-file`: Specify output Excel file path

### Examples

1. Run with specific solver options:
```bash
python model.py --solver cplex --solver-options threads=4 timelimit=3600
```

2. Run multiple scenarios:
```bash
python model.py --scenarios BAU AD --price-scenarios MarketPrice AvgPPAPrice
```

3. Specify custom input/output files:
```bash
python model.py --input-file data/custom_input.xlsx --output-file results/output.xlsx
```

## Input Data Format

The input Excel file should contain the following sheets:
- Plant data
- Time blocks
- Price scenarios
- [Add other required sheets]

## Output Format

The model generates an Excel file containing:
- Total generation by plant and year
- Net revenue calculations
- Capacity data
- Retirement schedules

## Error Handling

The model includes comprehensive error handling for:
- Missing input files
- Invalid solver configurations
- Scenario processing errors
- Result saving issues

## Contributing

[Add contribution guidelines if applicable]

## License

[Add license information]

## Contact

[Add contact information]

## Acknowledgments

[Add acknowledgments if applicable]
