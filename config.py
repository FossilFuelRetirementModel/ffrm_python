from pathlib import Path

class Config:
    DATA_DIR = Path("")
    INPUT_FILE = "250810 FFRM Data Input File - Philippines.xlsx"  # Updated to use new template
    EXCEL_PATH = DATA_DIR / INPUT_FILE
    
    # Sheet names - Updated for new template
    SHEETS = {
        'PLANT_DATA': 'Plant Data',  # Changed from COAL_PLANT
        'PRICE_DIST': 'Price_Distribution',
        'PRICE_GEN': 'Price_Gen',
        'FC_PPA': 'FC_PPA',
        'OTHER': 'Other',
        'DEFINITIONS': 'Definitions'  # New sheet
    }
    
    # Excel reading configurations - Updated for new template structure
    EXCEL_CONFIG = {
        'Definitions': {
            'usecols': 'A:I',  # Read all columns to find year information
            'skiprows': 0,
            'index_col': None  # Don't use index_col to preserve all columns
        },
        'PlantData': {  # Updated from CoalPlantData
            'usecols': 'A:J',  # 9 columns (0-8)
            'skiprows': 0,
            'header': 2,       # Use 3rd row as header (1-indexed)
            'index_col': 0
        },
        'Price_Distribution': {
            'time_blocks': {
                'usecols': 'B:M',  # 12 columns (1-12) for time blocks
                'skiprows': 1,
                'nrows': 1
            },
            'price_dist': {
                'usecols': 'A:M',  # 13 columns (0-12) for price distribution
                'skiprows': 2,
                'index_col': 0
            },
            'price_dur': {
                'usecols': 'M:N',  # 2 columns (12-13) for price duration
                'skiprows': 2,
                'index_col': 0
            }
        },
        'Price_Gen': {
            'usecols': 'A:AS',  # 49 columns (0-48) for technology-specific data
            'skiprows': 1,     # Skip first 2 rows (title and description)
            'index_col': None  # Don't use index_col to preserve row structure
        },
        'Other': {
            'usecols': 'A:C',  # 3 columns (0-2)
            'skiprows': 1,
            'index_col': None  # Don't use index_col to preserve column names
        },
        'FC_PPA': {
            'usecols': 'A:AU',  # 47 columns (0-46)
            'skiprows': 1,     # Updated skip rows
            'index_col': 0
        }
    }
    
    # Skip rows configuration (if needed separately)
    SKIP_ROWS = {
        'Definitions': 0,
        'PlantData': 1,        # Updated
        'Price_Distribution': 2,
        'FC_PPA': 1,           # Updated
        'Price_Gen': 1,        # Updated
        'Other': 1
    }
    
    # Technology types - Will be read from Excel file
    # TECHNOLOGY_TYPES will be dynamically set based on Excel data
    DEFAULT_TECHNOLOGY_TYPES = {
        'PWRCOA001': 'Coal',
        'PWROHC001': 'Oil Heavy',
        'PWROHC002': 'Oil Heavy',
        'PWRNGS001': 'Natural Gas',
        'PWRNGS002': 'Natural Gas',
        'PWROHC003': 'Oil Heavy'
    }
    
    # Excel cell positions for data extraction
    EXCEL_CELL_POSITIONS = {
        'year_range': {
            'start_year': {
                'row': 31,
                'col': 8,  # Column I (0-indexed) - where the actual year value is
                'description': 'Start Year cell position'
            },
            'end_year': {
                'row': 32,
                'col': 8,  # Column I (0-indexed) - where the actual year value is
                'description': 'End Year cell position'
            }
        },
        'technology_types': {
            'start_row': 23,
            'end_row': 28,
            'code_col': 7,    # Column H (0-indexed) - Technology codes
            'desc_col': 8,    # Column I (0-indexed) - Technology descriptions
            'description': 'Technology types table position'
        },
        'scenarios': {
            'start_row': 23,  # Updated to actual scenario data location (E23)
            'end_row': 31,    # Updated to include all scenarios (F31)
            'name_col': 4,    # Column E (0-indexed) - Scenario names
            'value_col': 5,   # Column F (0-indexed) - Scenario descriptions
            'description': 'Scenarios table position'
        },
        'price_scenarios': {
            'start_row': 42,  # Adjust based on actual Excel layout
            'end_row': 45,    # Adjust based on actual Excel layout
            'name_col': 7,    # Column H (0-indexed) - Price scenario names
            'value_col': 8,   # Column I (0-indexed) - Price scenario values
            'description': 'Price scenarios table position'
        }
    }
    
    # Technology-specific parameters
    TECH_SPECIFIC_PARAMS = [
        'Interest Rate',
        'Loan Term',
        'Generation Constraint (TWh)',
        'Marginal Revenue ($/MWh)'
    ]
    
    # Optimization parameter
    OPTCR = 0.06  # Optimality criterion
    
    # Year range - Will be read from Excel file
    # YEARS will be dynamically set based on Excel data
    DEFAULT_START_YEAR = 2025  # Updated to match new Excel file
    DEFAULT_END_YEAR = 2090    # Limited to 20 years for testing
    
    # Scenarios - Will be dynamically loaded from Excel
    SCENARIOS = {
        'BAU': 1   # Business as Usual (default)
    }
    
    # NEW: Intermediate decarbonization scenarios - Will be dynamically generated from Excel scenarios
    INTERMEDIATE_SCENARIOS = {}
    
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
    
    BASE_YEAR = 2025  # Base year for all calculations (updated to match Excel)
    INITIAL_YEAR = 2025  # Initial year of the model (updated to match Excel)
    
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