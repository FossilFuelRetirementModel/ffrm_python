from pathlib import Path

class Config:
    DATA_DIR = Path("")
    INPUT_FILE = "sample_input_file.xlsx"
    EXCEL_PATH = DATA_DIR / INPUT_FILE
    
    # Sheet names
    SHEETS = {
        'COAL_PLANT': 'CoalPlantData',
        'PRICE_DIST': 'Price_Distribution',
        'PRICE_GEN': 'Price_Gen',
        'FC_PPA': 'FC_PPA',
        'OTHER': 'Other'
    }
    
    # Excel reading configurations
    EXCEL_CONFIG = {
        'CoalPlantData': {
            'usecols': 'A:G',
            'skiprows': 2,
            'index_col': 0
        },
        'Price_Distribution': {
            'time_blocks': {
                'usecols': 'A:K',
                'skiprows': 2,
                'nrows': 1
            },
            'price_dist': {
                'usecols': 'A:K',
                'skiprows': 2,
                'nrows': 21,
                'index_col': 0
            },
            'price_dur': {
                'usecols': 'N:O',
                'skiprows': 2,
                'nrows': 10,
                'index_col': 0
            }
        },
        'Price_Gen': {
            'usecols': 'A:F',
            'skiprows': 2,
            'index_col': 0
        },
        'Other': {
            'usecols': 'A:C',
            'skiprows': 1,
            'index_col': 0
        },
        'FC_PPA': {
            'usecols': 'A:U',
            'skiprows': 4,
            'index_col': 0
        }
    }
    
    # Skip rows configuration (if needed separately)
    SKIP_ROWS = {
        'CoalPlantData': 2,
        'Price_Distribution': 2,
        'FC_PPA': 4,
        'Price_Gen': 2,
        'Other': 1
    }
    
    # Optimization parameter
    OPTCR = 0.06  # Optimality criterion
    
    # Year range
    YEARS = list(range(2021, 2041))  # 2021 to 2040
    
    # Scenarios
    SCENARIOS = {
        'BAU': 1,   # Business as Usual
        'AD': 0     # Accelerated Decarbonization
    }
    
    # Price scenarios
    PRICE_SCENARIOS = {
        'MarketPrice': 1,
        'AvgPPAPrice': 0
    }