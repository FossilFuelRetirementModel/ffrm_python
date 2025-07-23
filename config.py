from pathlib import Path

class Config:
    DATA_DIR = Path("")
    INPUT_FILE = "InputDataCoalUpdated.xlsx"
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
            # 'nrows': ,
            'index_col': 0
        },
        'Price_Distribution': {
            'time_blocks': {
                'usecols': 'B:K',
                'skiprows': 1,
                'nrows': 1
            },
            'price_dist': {
                'usecols': 'A:K',
                'skiprows': 2,
                # 'nrows': 21,
                'index_col': 0
            },
            'price_dur': {
                'usecols': 'N:O',
                'skiprows': 2,
                # 'nrows': 10,
                'index_col': 0
            }
        },
        'Price_Gen': {
            'usecols': 'A:E',
            'skiprows': 2,
            'index_col': 0
        },
        'Other': {
            'usecols': 'A:B',
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
    
    
    # Scenarios
    SCENARIOS = {
        'BAU': 1,   # Business as Usual
        'AD': 0     # Accelerated Decarbonization
    }
    
    # NEW: Intermediate decarbonization scenarios
    INTERMEDIATE_SCENARIOS = {
        'AD_25': 0.25,   # 25% of the way from BAU to AD (1/4 AD)
        'AD_50': 0.50,   # 50% of the way from BAU to AD (1/2 AD) 
        'AD_75': 0.75    # 75% of the way from BAU to AD (3/4 AD)
    }
    
    # Price scenarios
    PRICE_SCENARIOS = {
        'MarketPrice': 1,
        'AvgPPAPrice': 0
    }
    
    # ============================================================================
    # NEW: Time and Conversion Constants (moved from hardcoded values)
    # ============================================================================
    
    # Time constants
    HOURS_PER_DAY = 24.0  # Hours in a day
    HOURS_PER_YEAR = 8760.0  # Hours in a year (365 * 24)
    DAYS_PER_YEAR = 365.0  # Days in a year
    
    # Conversion factors
    MW_TO_GW = 1000.0  # Convert MW to GW
    GW_TO_MW = 1000.0  # Convert GW to MW
    USD_TO_THOUSANDS = 1000.0  # Convert USD to thousands
    USD_TO_MILLIONS = 1e6  # Convert USD to millions
    TWH_TO_MWH = 1e6  # Convert TWh to MWh
    
    # ============================================================================
    # NEW: Load Factor Constants (moved from hardcoded values)
    # ============================================================================
    
    # Load factor thresholds
    MAX_LOAD_FACTOR = 0.75  # Maximum plant load factor (75%)
    MAX_LOAD_FACTOR_ALT = 0.74  # Alternative maximum load factor (74%)
    MIN_PLF_THRESHOLD = 0.25  # Minimum PLF threshold for debugging
    
    # ============================================================================
    # NEW: Cost and Price Constants (moved from hardcoded values)
    # ============================================================================
    
    # Default costs and prices
    DEFAULT_COST_PER_MW_MarketPrice = 100.0  # Default cost per MW (USD/MW)
    DEFAULT_FC_PPA_VALUE = 100.0  # Default FC_PPA value when not found
    
    # ============================================================================
    # NEW: Base Year and Time Period Constants (moved from hardcoded values)
    # ============================================================================
    
    BASE_YEAR = 2024  # The START YEAR of the model
    INITIAL_YEAR = BASE_YEAR  
    END_YEAR = 2050  # The END YEAR of the model
    # Year range
    YEARS = list(range(INITIAL_YEAR, END_YEAR + 1))
    # ============================================================================
    # NEW: Plant Life Categories (moved from hardcoded values)
    # ============================================================================
    
    YOUNG_PLANT_THRESHOLD = 10  # Plants younger than this are "young"
    OLD_PLANT_THRESHOLD = 30  # Plants older than this are "old"
    
    # ============================================================================
    # NEW: Plant Life Categories (moved from hardcoded values)
    # ============================================================================
    
    YOUNG_PLANT_THRESHOLD = 10  # Plants younger than this are "young"
    OLD_PLANT_THRESHOLD = 30  # Plants older than this are "old"
    
    # ============================================================================
    # NEW: Capacity and Retirement Constants (moved from hardcoded values)
    # ============================================================================
    
    MAX_RETIREMENTS_PER_PLANT = 1  # Maximum number of retirements per plant
    FIXED_CAPACITY_EXPIRED = 0.0  # Fixed capacity for expired plants
    
    # ============================================================================
    # NEW: Discount Rate Constants (moved from hardcoded values)
    # ============================================================================
    
    DISCOUNT_RATE = 0.06  # 6% discount rate for calculations
    
    # ============================================================================
    # NEW: File Naming Constants (moved from hardcoded values)
    # ============================================================================
    
    # Output file names
    DEFAULT_OUTPUT_FILE = "Results.xlsx"
    LP_FILE_TEMPLATE = "{scenario}_{price_scenario}.lp"
    SCENARIO_OUTPUT_TEMPLATE = "{key}_results.xlsx"
    
    # ============================================================================
    # NEW: Solver Configuration (moved from hardcoded values)
    # ============================================================================
    
    # Default solver settings
    DEFAULT_SOLVER = 'gurobi'
    AVAILABLE_SOLVERS = ['glpk', 'cplex', 'gurobi', 'cbc']
    
    # ============================================================================
    # NEW: Validation Constants (moved from hardcoded values)
    # ============================================================================
    
    # Validation thresholds
    TOLERANCE = 1e-6  # Tolerance for floating point comparisons
    MIN_REQUIRED_CAPACITY_FACTOR = 0.75  # Factor for minimum capacity calculations