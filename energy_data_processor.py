import pandas as pd
import logging
from pathlib import Path
from config import Config
from typing import Dict, List
from dataclasses import dataclass
# from pyomo.environ import *

# Configure logging
def setup_logging(output_dir=None):
    """Setup logging with optional output directory"""
    log_file = 'data_loading.log'
    if output_dir:
        log_file = str(Path(output_dir) / 'data_loading.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Initialize logging without output directory for standalone use
setup_logging()
logger = logging.getLogger(__name__)

@dataclass
class ModelData:
    """Class to hold all model data structures"""
    # Basic sets
    years: List[int]              # y: Years from 2021 to 2070
    plants: List[str]             # g: Plant identifiers (from plant_data)
    time_blocks: List[str]        # t: Time blocks (from price_distribution)
    scenarios: Dict[str, int]     # s: BAU and AD scenarios
    price_scenarios: Dict[str, int]  # p: Market Price and PPA Price scenarios
    technologies: List[str]       # tech: Technology types (PWRCOA001, etc.)
    
    # Parameter data
    gen_data: pd.DataFrame        # GenData(g,*)  Plant-level data
    price_gen: pd.DataFrame       # Price_gen(y,*) Forecasted average price and total generation per year
    price_dist: pd.DataFrame      # Price_dist(y,t) Distribution of prices as multiple of average price
    price_dur: pd.DataFrame       # Price_dur(t,*) Duration of price blocks
    other: pd.DataFrame          # Other(*,*) Other parameters (now technology-specific)
    fc_ppa: pd.DataFrame         # FC_PPA(g,y) Mandatory capacity payment
    tech_params: pd.DataFrame    # Technology-specific parameters

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataframe by removing nonsense indices and handling duplicates."""
    if df is None or df.empty:
        return df
    
    # Remove nonsense indices using boolean indexing
    valid_mask = ~(df.index.isna() | (df.index == " "))
    if not valid_mask.all():
        print(f"Removing nonsense indices: {list(df.index[~valid_mask])}")
        df = df[valid_mask]

    # Handle duplicates using pandas built-in
    if df.index.duplicated().any():
        print(f"Warning: Duplicate indices found")
        print("Duplicate indices:", df.index[df.index.duplicated()].tolist())
        df = df[~df.index.duplicated(keep='first')]
    
    return df

def process_technology_specific_data(other_df: pd.DataFrame) -> pd.DataFrame:
    """Process technology-specific data from the Other sheet using pandas operations."""
    if other_df is None or other_df.empty:
        logger.warning("DEFAULT: No technology-specific data found in Excel")
        return pd.DataFrame()
    
    other_df = clean_dataframe(other_df)
    
    # Define target parameters
    target_params = [
        'DiscountRate', 'Straight-line depreciation', 'CoalCapex $/kW',
        'CostEsc_Lessthan10', 'CostEsc_10-30years', 'CostEsc_30plus',
        'MinPLF', 'MaxPLF', 'MaxLife', 'Interest Rate', 'Loan Term'
    ]
    
    logger.info("EXCEL_READ: Processing technology-specific parameters from Other sheet...")
    
    # Filter rows for target parameters and valid technology
    mask = (other_df['Other'].isin(target_params) & 
            other_df['Unnamed: 1'].notna() & 
            (other_df['Unnamed: 1'] != ''))
    
    filtered_df = other_df[mask].copy()
    
    if filtered_df.empty:
        logger.warning("DEFAULT: No technology-specific parameters found in Excel")
        return pd.DataFrame()
    
    # Pivot the data to get parameters as columns and technologies as index
    tech_params = filtered_df.pivot(index='Unnamed: 1', columns='Other', values='Unnamed: 2')
    
    # Log found parameters
    logger.info("EXCEL_READ: Technology-specific parameters found in Excel:")
    for tech in tech_params.index:
        for param in tech_params.columns:
            value = tech_params.loc[tech, param]
            if pd.notna(value):
                logger.info(f"  EXCEL_READ: {tech} - {param} = {value}")
    
    logger.info(f"EXCEL_READ: Processed {len(tech_params.columns)} parameters for {len(tech_params)} technologies")
    return tech_params

def process_price_gen_data(price_gen_df: pd.DataFrame, years: list) -> pd.DataFrame:
    """Process price generation data with technology-specific and scenario-specific constraints."""
    if price_gen_df is None or price_gen_df.empty:
        return pd.DataFrame()
    
    # Just remove completely empty rows and columns
    price_gen_df = price_gen_df.dropna(how='all').dropna(axis=1, how='all')
    
    logger.info(f"PRICE_GEN: Processing data with shape: {price_gen_df.shape}")
    
    # Get column headers from first row (index 0) where years are located
    headers = price_gen_df.iloc[0]
    logger.info(f"PRICE_GEN: Headers from first row: {list(headers)[:10]}")
    
    # Technology and scenario columns are in columns 0 and 1
    tech_col = 0  # Technology column
    scen_col = 1  # Scenario column
    
    logger.info(f"PRICE_GEN: Using columns tech={tech_col}, scenario={scen_col}")
    
    # Get data rows starting from the second row (skip header)
    data_rows = price_gen_df.iloc[1:].copy()
    
    if data_rows.empty:
        logger.warning("PRICE_GEN: No data rows found")
        return pd.DataFrame()
    
    logger.info(f"PRICE_GEN: Found {len(data_rows)} data rows")
    
    # Debug: Show the first few rows to understand the data structure
    logger.info(f"PRICE_GEN: First few data rows:")
    for i in range(min(10, len(data_rows))):
        tech_val = data_rows.iloc[i, tech_col]
        scen_val = data_rows.iloc[i, scen_col]
        logger.info(f"  Row {i}: tech='{tech_val}', scenario='{scen_val}'")
    
    # Filter out rows with empty technology or scenario
    valid_mask = (data_rows.iloc[:, tech_col].notna() & 
                  (data_rows.iloc[:, tech_col].astype(str).str.strip() != '') &
                  (data_rows.iloc[:, tech_col].astype(str).str.strip() != 'Technology') &
                  data_rows.iloc[:, scen_col].notna() & 
                  (data_rows.iloc[:, scen_col].astype(str).str.strip() != '') &
                  (data_rows.iloc[:, scen_col].astype(str).str.strip() != 'Scenario') &
                  (data_rows.iloc[:, scen_col].astype(str).str.strip() != ' '))
    
    data_rows = data_rows[valid_mask].copy()
    logger.info(f"PRICE_GEN: After filtering, {len(data_rows)} valid tech-scenario combinations")
    
    # Create technology-scenario keys
    data_rows['tech_scenario'] = (data_rows.iloc[:, tech_col].astype(str) + '_' + 
                                 data_rows.iloc[:, scen_col].astype(str))
    
    # Identify year columns from headers (starting from column 2)
    year_cols_map = {}
    for i, header in enumerate(headers):
        if i < 2:  # Skip tech and scenario columns
            continue
        
        # Try to parse year from header
        try:
            if hasattr(header, 'year'):
                y = int(header.year)
            elif isinstance(header, (int, float)):
                y = int(header)
            elif isinstance(header, str):
                # Handle datetime strings like "2025-01-01 00:00:00"
                if '-' in str(header):
                    y = pd.to_datetime(header).year
                else:
                    y = int(header)
            elif hasattr(header, 'dtype') and 'float' in str(header.dtype):
                # Handle numpy float values (these are the year data)
                y = int(header)
            else:
                continue
                
            if y in years:
                year_cols_map[y] = i  # Use column index directly
        except Exception:
            continue
    
    if not year_cols_map:
        logger.warning(f"PRICE_GEN: No year columns detected. Available headers: {list(headers)[:10]}")
        return pd.DataFrame()
    
    logger.info(f"PRICE_GEN: Found year columns: {sorted(year_cols_map.keys())}")
    
    # Build generation targets
    year_data = {y: {} for y in sorted(year_cols_map.keys())}
    for y, col_idx in year_cols_map.items():
        for _, row in data_rows.iterrows():
            val = row.iloc[col_idx]
            if pd.notna(val):
                key = row['tech_scenario']
                year_data[y][key] = val
    
    result_df = pd.DataFrame(year_data)
    logger.info(f"PRICE_GEN: Final result shape: {result_df.shape}")
    logger.info(f"PRICE_GEN: Technology-scenario combinations: {result_df.index.tolist()}")
    
    # 输出 generation target 数据
    logger.info("PRICE_GEN: Generation Target Data:")
    logger.info("=" * 80)
    for tech_scenario in result_df.index:
        logger.info(f"Technology-Scenario: {tech_scenario}")
        for year in result_df.columns:
            value = result_df.loc[tech_scenario, year]
            if pd.notna(value):
                logger.info(f"  {year}: {value:.2f}")
        logger.info("-" * 40)
    
    return result_df

def normalize_plant_data(plant_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Plant Data: map header names to canonical fields, coerce dtypes, strip tech codes.
    Assumes the Excel was read with the 3rd row as header (config header=2)."""
    if plant_df is None or plant_df.empty:
        return plant_df
    df = plant_df.copy()
    # Standardize column names by mapping known headers to canonical names
    rename_map = {
        'Variable Cost ($/MWh)': 'COST',
        'Fixed Cost ($/MWh)': 'FIXED_COST',
        'PPA Price ($/MWh)': 'AvgPPAPrice',
        'Market Price ($/MWh)': 'MarketPrice',
        'Capacity (MW)': 'CAPACITY',
        'Start Year': 'STARTYEAR',
        'Plant Type': 'TECHNOLOGY',
        'Price Regime': 'PriceRegime',
        'ContractPriceMW': 'ContractPriceMW',
    }
    for src, dst in rename_map.items():
        if src in df.columns:
            df.rename(columns={src: dst}, inplace=True)
    # Drop rows with empty index (no plant name)
    df = df[~df.index.isna()].copy()
    # Coerce numeric columns
    for col in ['COST', 'FIXED_COST', 'PPAPrice', 'MarketPrice', 'CAPACITY', 'STARTYEAR', 'ContractPriceMW']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Clean technology codes
    if 'TECHNOLOGY' in df.columns:
        df['TECHNOLOGY'] = df['TECHNOLOGY'].astype(str).str.strip()
    return df

def initialize_model_data(data: dict) -> ModelData:
    """Initialize model data structures from loaded Excel data."""
    # Clean all DataFrames except price_gen (which needs special handling)
    for key, df in data.items():
        if isinstance(df, pd.DataFrame) and key != 'price_gen':
            data[key] = clean_dataframe(df)
    
    # Extract basic parameters
    start_year = data.get('start_year', Config.DEFAULT_START_YEAR)
    end_year = data.get('end_year', Config.DEFAULT_END_YEAR)
    years = list(range(start_year, end_year + 1))
    
    technology_types = data.get('technology_types', Config.DEFAULT_TECHNOLOGY_TYPES)
    technologies = list(technology_types.keys())
    
    # Get scenarios from Excel data (or use defaults)
    scenarios = data.get('scenarios', Config.SCENARIOS)
    price_scenarios = data.get('price_scenarios', Config.PRICE_SCENARIOS)
    
    # Process data using pandas operations
    tech_params = process_technology_specific_data(data.get('other', pd.DataFrame()))
    # TEMP OVERRIDE: Set MaxLife to 100 for all technologies
    if not tech_params.empty and 'MaxLife' in tech_params.columns:
        tech_params.loc[:, 'MaxLife'] = 80
    processed_price_gen = process_price_gen_data(data.get('price_gen', pd.DataFrame()), years)
    plant_df_raw = data.get('plant_data', pd.DataFrame())
    plant_df = normalize_plant_data(plant_df_raw)
    
    # Clean time_blocks to remove invalid column names
    time_blocks = data.get('price_distribution', pd.DataFrame()).columns.tolist() if 'price_distribution' in data else []
    # Remove 'Unnamed:' columns and other invalid time block names
    valid_time_blocks = [col for col in time_blocks if not col.startswith('Unnamed:') and col != '']
    logger.info(f"Cleaned time_blocks: removed invalid columns, kept {len(valid_time_blocks)} valid time blocks")
    
    # Fix price_dist index to use integer years instead of timestamps
    price_dist = data.get('price_distribution', pd.DataFrame())
    if not price_dist.empty and hasattr(price_dist.index[0], 'year'):
        # Convert timestamp index to integer years
        price_dist.index = [idx.year if hasattr(idx, 'year') else idx for idx in price_dist.index]
        logger.info(f"Fixed price_dist index: converted timestamps to integer years")
    
    # Clean price_dist columns to match valid time blocks
    if not price_dist.empty:
        price_dist = price_dist[valid_time_blocks]
        logger.info(f"Cleaned price_dist columns to match valid time blocks")
    
    # Log summary using pandas info
    logger.info("EXCEL_READ: Data loading summary:")
    logger.info(f"  EXCEL_READ: Plant data shape: {data.get('plant_data', pd.DataFrame()).shape}")
    logger.info(f"  EXCEL_READ: Technology parameters shape: {tech_params.shape if not tech_params.empty else 'No tech params'}")
    logger.info(f"  EXCEL_READ: Year range: {start_year} - {end_year} ({len(years)} years)")
    logger.info(f"  EXCEL_READ: Technology types: {len(technologies)} types - {technologies}")
    logger.info(f"  EXCEL_READ: Scenarios: {len(scenarios)} scenarios - {list(scenarios.keys())}")
    logger.info(f"  EXCEL_READ: Price scenarios: {len(price_scenarios)} scenarios - {list(price_scenarios.keys())}")
    
    return ModelData(
        years=years,
        plants=plant_df.index.tolist() if not plant_df.empty else [],
        time_blocks=valid_time_blocks,  # Use cleaned time blocks
        scenarios=scenarios,  # Use dynamically read scenarios
        price_scenarios=price_scenarios,  # Use dynamically read price scenarios
        technologies=technologies,
        
        # Data tables
        gen_data=plant_df,
        price_gen=processed_price_gen,
        price_dist=price_dist,  # Use the fixed price_dist
        price_dur=data.get('price_dur', pd.DataFrame()),
        other=data.get('other', pd.DataFrame()),
        fc_ppa=data.get('fc_ppa', pd.DataFrame()),
        tech_params=tech_params
    )

def generate_intermediate_scenarios(model_data: ModelData) -> ModelData:
    """Generate intermediate decarbonization scenarios between BAU and AD using pandas operations."""
    try:
        print("Generating intermediate decarbonization scenarios...")
        
        if model_data.price_gen.empty:
            print("Warning: No price_gen data available")
            return model_data
        
        # Get available scenarios from model_data
        available_scenarios = list(model_data.scenarios.keys())
        
        # Find BAU scenario and AD scenarios
        bau_scenario = None
        ad_scenarios = []
        
        for scenario in available_scenarios:
            if scenario == 'BAU':
                bau_scenario = scenario
            elif scenario.startswith('AD_'):
                ad_scenarios.append(scenario)
        
        if not bau_scenario:
            print("Warning: Could not find BAU scenario")
            return model_data
        
        if not ad_scenarios:
            print("Warning: Could not find AD scenarios")
            return model_data
        
        # Create extended price_gen DataFrame
        extended_price_gen = model_data.price_gen.copy()
        
        # Generate intermediate scenarios for each AD scenario
        intermediate_scenarios = {}
        
        for ad_scenario in ad_scenarios:
            # Extract percentage from scenario name (e.g., AD_20 -> 0.20)
            try:
                percentage = int(ad_scenario.split('_')[1]) / 100.0
                intermediate_scenarios[ad_scenario] = percentage
            except (IndexError, ValueError):
                print(f"Warning: Could not parse percentage from scenario {ad_scenario}")
                continue
            
            print(f"\nGenerating {ad_scenario} (factor: {percentage}):")
            
            # For now, we'll use a simple approach: scale the generation targets
            # In a more sophisticated approach, you might want to interpolate between BAU and a full AD scenario
            
            # Get the generation column for this scenario
            scenario_col = None
            for col in extended_price_gen.columns:
                if ad_scenario in str(col):
                    scenario_col = col
                    break
            
            if scenario_col:
                # The scenario data is already in the Excel file, so we don't need to calculate it
                print(f"  Using existing data for {ad_scenario}")
            else:
                print(f"  Warning: Could not find data column for {ad_scenario}")
        
        # Create updated scenarios dictionary with all scenarios
        all_scenarios = model_data.scenarios.copy()
        
        # Create new ModelData object
        updated_model_data = ModelData(
            years=model_data.years,
            plants=model_data.plants,
            time_blocks=model_data.time_blocks,
            scenarios=all_scenarios,
            price_scenarios=model_data.price_scenarios,
            technologies=model_data.technologies,
            
            # Data tables
            gen_data=model_data.gen_data,
            price_gen=extended_price_gen,
            price_dist=model_data.price_dist,
            price_dur=model_data.price_dur,
            other=model_data.other,
            fc_ppa=model_data.fc_ppa,
            tech_params=model_data.tech_params
        )
        
        print(f"\nSuccessfully processed scenarios: {list(all_scenarios.keys())}")
        return updated_model_data
        
    except Exception as e:
        print(f"Error generating intermediate scenarios: {str(e)}")
        raise

def extract_technology_types_from_definitions(definitions_df: pd.DataFrame) -> dict:
    """Extract technology types from the Definitions sheet using pandas operations."""
    try:
        # Get cell positions from config
        tech_config = Config.EXCEL_CELL_POSITIONS['technology_types']
        start_row = tech_config['start_row']
        end_row = tech_config['end_row']
        code_col = tech_config['code_col']
        desc_col = tech_config['desc_col']
        
        logger.info(f"EXCEL_READ: Extracting technology types from rows {start_row}-{end_row}, columns {code_col}-{desc_col}")
        
        # Extract the relevant slice using pandas iloc
        if len(definitions_df) > end_row and len(definitions_df.columns) > max(code_col, desc_col):
            tech_slice = definitions_df.iloc[start_row:end_row+1, [code_col, desc_col]]
            
            # Filter for valid technology codes
            valid_mask = (tech_slice.iloc[:, 0].notna() & 
                         (tech_slice.iloc[:, 0].astype(str).str.strip() != '') &
                         (tech_slice.iloc[:, 0].astype(str).str.strip() != 'nan') &
                         tech_slice.iloc[:, 0].astype(str).str.startswith('PWR'))
            
            valid_techs = tech_slice[valid_mask]
            
            if not valid_techs.empty:
                # Create dictionary using pandas operations
                tech_codes = valid_techs.iloc[:, 0].astype(str).str.strip()
                tech_descs = valid_techs.iloc[:, 1].astype(str).str.strip().fillna(tech_codes)
                
                technology_types = dict(zip(tech_codes, tech_descs))
                
                # Log found technologies
                logger.info("EXCEL_READ: Technology types found in Excel:")
                for tech_code, tech_desc in technology_types.items():
                    logger.info(f"  EXCEL_READ: {tech_code} - {tech_desc}")
                
                logger.info(f"EXCEL_READ: Extracted {len(technology_types)} technology types: {list(technology_types.keys())}")
                return technology_types
        
        logger.warning("DEFAULT: No technology types found in Excel, using default values from code")
        logger.info("DEFAULT: Technology types from code:")
        for tech_code, tech_desc in Config.DEFAULT_TECHNOLOGY_TYPES.items():
            logger.info(f"  DEFAULT: {tech_code} - {tech_desc}")
        return Config.DEFAULT_TECHNOLOGY_TYPES
        
    except Exception as e:
        logger.error(f"Error extracting technology types: {str(e)}")
        logger.info("DEFAULT: Using technology types from code due to error")
        return Config.DEFAULT_TECHNOLOGY_TYPES

def extract_scenarios_from_definitions(definitions_df: pd.DataFrame) -> dict:
    """Extract scenarios from the Definitions sheet using pandas operations."""
    try:
        # Get cell positions from config
        scenario_config = Config.EXCEL_CELL_POSITIONS['scenarios']
        start_row = scenario_config['start_row']
        end_row = scenario_config['end_row']
        name_col = scenario_config['name_col']
        value_col = scenario_config['value_col']
        
        logger.info(f"EXCEL_READ: Extracting scenarios from rows {start_row}-{end_row}, columns {name_col}-{value_col}")
        
        # Extract the relevant slice using pandas iloc
        if len(definitions_df) > end_row and len(definitions_df.columns) > max(name_col, value_col):
            scenario_slice = definitions_df.iloc[start_row:end_row+1, [name_col, value_col]]
            
            # Filter for valid scenario names
            valid_mask = (scenario_slice.iloc[:, 0].notna() & 
                         (scenario_slice.iloc[:, 0].astype(str).str.strip() != '') &
                         (scenario_slice.iloc[:, 0].astype(str).str.strip() != 'nan'))
            
            valid_scenarios = scenario_slice[valid_mask]
            
            if not valid_scenarios.empty:
                # Create dictionary using pandas operations
                scenario_names = valid_scenarios.iloc[:, 0].astype(str).str.strip()
                scenario_descriptions = valid_scenarios.iloc[:, 1].astype(str).str.strip().fillna('')
                
                # Assign values based on scenario type
                scenarios = {}
                for name, desc in zip(scenario_names, scenario_descriptions):
                    if name == 'BAU':
                        scenarios[name] = 1  # Active scenario
                    elif name.startswith('AD_'):
                        scenarios[name] = 0  # Intermediate scenarios (can be activated later)
                    else:
                        scenarios[name] = 0  # Default for other scenarios
                
                # Log found scenarios
                logger.info("EXCEL_READ: Scenarios found in Excel:")
                for scenario_name, scenario_value in scenarios.items():
                    status = "Active" if scenario_value == 1 else "Inactive"
                    desc = scenario_descriptions[scenario_names == scenario_name].iloc[0] if scenario_name in scenario_names.values else ""
                    logger.info(f"  EXCEL_READ: {scenario_name} = {scenario_value} ({status}) - {desc}")
                
                logger.info(f"EXCEL_READ: Extracted {len(scenarios)} scenarios: {list(scenarios.keys())}")
                return scenarios
        
        logger.warning("DEFAULT: No scenarios found in Excel, using default values from code")
        logger.info("DEFAULT: Scenarios from code:")
        for scenario_name, scenario_value in Config.SCENARIOS.items():
            status = "Active" if scenario_value == 1 else "Inactive"
            logger.info(f"  DEFAULT: {scenario_name} = {scenario_value} ({status})")
        return Config.SCENARIOS
        
    except Exception as e:
        logger.error(f"Error extracting scenarios: {str(e)}")
        logger.info("DEFAULT: Using scenarios from code due to error")
        return Config.SCENARIOS

def extract_price_scenarios_from_definitions(definitions_df: pd.DataFrame) -> dict:
    """Extract price scenarios from the Definitions sheet using pandas operations."""
    try:
        # Get cell positions from config
        price_scenario_config = Config.EXCEL_CELL_POSITIONS['price_scenarios']
        start_row = price_scenario_config['start_row']
        end_row = price_scenario_config['end_row']
        name_col = price_scenario_config['name_col']
        value_col = price_scenario_config['value_col']
        
        logger.info(f"EXCEL_READ: Extracting price scenarios from rows {start_row}-{end_row}, columns {name_col}-{value_col}")
        
        # Extract the relevant slice using pandas iloc
        if len(definitions_df) > end_row and len(definitions_df.columns) > max(name_col, value_col):
            price_scenario_slice = definitions_df.iloc[start_row:end_row+1, [name_col, value_col]]
            
            # Filter for valid price scenario names
            valid_mask = (price_scenario_slice.iloc[:, 0].notna() & 
                         (price_scenario_slice.iloc[:, 0].astype(str).str.strip() != '') &
                         (price_scenario_slice.iloc[:, 0].astype(str).str.strip() != 'nan'))
            
            valid_price_scenarios = price_scenario_slice[valid_mask]
            
            if not valid_price_scenarios.empty:
                # Create dictionary using pandas operations
                price_scenario_names = valid_price_scenarios.iloc[:, 0].astype(str).str.strip()
                price_scenario_values = valid_price_scenarios.iloc[:, 1].astype(float)
                
                price_scenarios = dict(zip(price_scenario_names, price_scenario_values))
                
                # Log found price scenarios
                logger.info("EXCEL_READ: Price scenarios found in Excel:")
                for scenario_name, scenario_value in price_scenarios.items():
                    status = "Active" if scenario_value == 1 else "Inactive"
                    logger.info(f"  EXCEL_READ: {scenario_name} = {scenario_value} ({status})")
                
                logger.info(f"EXCEL_READ: Extracted {len(price_scenarios)} price scenarios: {list(price_scenarios.keys())}")
                return price_scenarios
        
        logger.warning("DEFAULT: No price scenarios found in Excel, using default values from code")
        logger.info("DEFAULT: Price scenarios from code:")
        for scenario_name, scenario_value in Config.PRICE_SCENARIOS.items():
            status = "Active" if scenario_value == 1 else "Inactive"
            logger.info(f"  DEFAULT: {scenario_name} = {scenario_value} ({status})")
        return Config.PRICE_SCENARIOS
        
    except Exception as e:
        logger.error(f"Error extracting price scenarios: {str(e)}")
        logger.info("DEFAULT: Using price scenarios from code due to error")
        return Config.PRICE_SCENARIOS

def extract_year_range_from_definitions(definitions_df: pd.DataFrame) -> tuple:
    """Extract start and end years from the Definitions sheet using pandas operations."""
    try:
        # Get cell positions from config
        year_config = Config.EXCEL_CELL_POSITIONS['year_range']
        start_year_pos = year_config['start_year']
        end_year_pos = year_config['end_year']
        
        logger.info(f"EXCEL_READ: Extracting year range from positions: Start Year at [{start_year_pos['row']},{start_year_pos['col']}], End Year at [{end_year_pos['row']},{end_year_pos['col']}]")
        
        start_year = None
        end_year = None
        
        # Try to get years from specified positions
        if (len(definitions_df) > start_year_pos['row'] and 
            len(definitions_df.columns) > start_year_pos['col']):
            start_year_cell = definitions_df.iloc[start_year_pos['row'], start_year_pos['col']]
            start_year = _extract_year_from_cell(start_year_cell)
            if start_year:
                logger.info(f"EXCEL_READ: Found Start Year: {start_year} from cell value: {start_year_cell}")
        
        if (len(definitions_df) > end_year_pos['row'] and 
            len(definitions_df.columns) > end_year_pos['col']):
            end_year_cell = definitions_df.iloc[end_year_pos['row'], end_year_pos['col']]
            end_year = _extract_year_from_cell(end_year_cell)
            if end_year:
                logger.info(f"EXCEL_READ: Found End Year: {end_year} from cell value: {end_year_cell}")
        
        # If not found, search for labels using pandas string operations
        if start_year is None or end_year is None:
            logger.info("EXCEL_READ: Searching for year labels and extracting values from adjacent cells...")
            
            # Convert all cells to string and search for year labels
            str_df = definitions_df.astype(str)
            
            # Find rows containing year labels
            start_mask = str_df.apply(lambda x: x.str.contains('Start Year', na=False)).any(axis=1)
            end_mask = str_df.apply(lambda x: x.str.contains('End Year', na=False)).any(axis=1)
            
            if start_mask.any() and start_year is None:
                start_row_idx = start_mask.idxmax()
                start_col_idx = str_df.loc[start_row_idx].str.contains('Start Year', na=False).idxmax()
                if start_col_idx + 1 < len(definitions_df.columns):
                    year_cell = definitions_df.iloc[start_row_idx, start_col_idx + 1]
                    start_year = _extract_year_from_cell(year_cell)
                    if start_year:
                        logger.info(f"EXCEL_READ: Found Start Year: {start_year} from adjacent cell: {year_cell}")
            
            if end_mask.any() and end_year is None:
                end_row_idx = end_mask.idxmax()
                end_col_idx = str_df.loc[end_row_idx].str.contains('End Year', na=False).idxmax()
                if end_col_idx + 1 < len(definitions_df.columns):
                    year_cell = definitions_df.iloc[end_row_idx, end_col_idx + 1]
                    end_year = _extract_year_from_cell(year_cell)
                    if end_year:
                        logger.info(f"EXCEL_READ: Found End Year: {end_year} from adjacent cell: {year_cell}")
        
        # Use defaults if not found
        if start_year is None:
            start_year = Config.DEFAULT_START_YEAR
            logger.warning(f"DEFAULT: Start year not found in Excel, using default from code: {start_year}")
        
        if end_year is None:
            end_year = Config.DEFAULT_END_YEAR
            logger.warning(f"DEFAULT: End year not found in Excel, using default from code: {end_year}")
        
        logger.info(f"EXCEL_READ: Final year range: {start_year} - {end_year}")
        return start_year, end_year
        
    except Exception as e:
        logger.error(f"Error extracting year range: {str(e)}")
        logger.info(f"DEFAULT: Using year range from code due to error: {Config.DEFAULT_START_YEAR} - {Config.DEFAULT_END_YEAR}")
        return Config.DEFAULT_START_YEAR, Config.DEFAULT_END_YEAR

def _extract_year_from_cell(cell_value) -> int:
    """Helper function to extract year from cell value."""
    try:
        # Handle pandas Timestamp/datetime objects
        if hasattr(cell_value, 'year'):
            return int(cell_value.year)
        
        # Handle string values
        year_str = str(cell_value).strip()
        if year_str and year_str != 'nan':
            # Handle datetime strings like "2025-01-01 00:00:00"
            if '-' in year_str:
                # Extract year from datetime string
                year_part = year_str.split('-')[0]
                return int(year_part)
            # Handle simple year strings
            else:
                return int(year_str)
    except (ValueError, IndexError, AttributeError):
        pass
    return None

def load_excel_data(file_path: Path) -> dict:
    """Load all required data from Excel file using pandas operations."""
    try:
        logger.info(f"EXCEL_READ: Loading data from Excel file: {file_path}")
        
        # Read Definitions sheet first
        definitions = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['DEFINITIONS'],
            **Config.EXCEL_CONFIG['Definitions']
        )
        
        # Extract metadata using pandas operations
        start_year, end_year = extract_year_range_from_definitions(definitions)
        technology_types = extract_technology_types_from_definitions(definitions)
        scenarios = extract_scenarios_from_definitions(definitions)
        price_scenarios = extract_price_scenarios_from_definitions(definitions)
        
        # Read all sheets using dictionary comprehension
        sheet_data = {
            'plant_data': pd.read_excel(file_path, sheet_name=Config.SHEETS['PLANT_DATA'], **Config.EXCEL_CONFIG['PlantData']),
            'price_distribution': pd.read_excel(file_path, sheet_name=Config.SHEETS['PRICE_DIST'], **Config.EXCEL_CONFIG['Price_Distribution']['price_dist']),
            'time_blocks': pd.read_excel(file_path, sheet_name=Config.SHEETS['PRICE_DIST'], **Config.EXCEL_CONFIG['Price_Distribution']['time_blocks']),
            'price_dur': pd.read_excel(file_path, sheet_name=Config.SHEETS['PRICE_DIST'], **Config.EXCEL_CONFIG['Price_Distribution']['price_dur']),
            'price_gen': pd.read_excel(file_path, sheet_name=Config.SHEETS['PRICE_GEN'], **Config.EXCEL_CONFIG['Price_Gen']),
            'other': pd.read_excel(file_path, sheet_name=Config.SHEETS['OTHER'], **Config.EXCEL_CONFIG['Other']),
            'fc_ppa': pd.read_excel(file_path, sheet_name=Config.SHEETS['FC_PPA'], **Config.EXCEL_CONFIG['FC_PPA'])
        }
        
        logger.info("EXCEL_READ: Successfully loaded all Excel sheets:")
        for sheet_name, df in sheet_data.items():
            logger.info(f"  EXCEL_READ: {sheet_name}: {df.shape}")
        
        return {
            'definitions': definitions,
            'start_year': start_year,
            'end_year': end_year,
            'technology_types': technology_types,
            'scenarios': scenarios,
            'price_scenarios': price_scenarios,
            **sheet_data
        }

    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise
    

if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("STARTING DATA LOADING PROCESS")
        logger.info("=" * 60)
        
        # Load Excel data
        raw_data = load_excel_data(Config.EXCEL_PATH)
        
        # Initialize model data structures
        model_data = initialize_model_data(raw_data)
        
        # Print key data for verification
        logger.info("\n" + "=" * 60)
        logger.info("MODEL DATA OVERVIEW")
        logger.info("=" * 60)
        
        logger.info(f"Years: {model_data.years}")
        logger.info(f"Number of years: {len(model_data.years)}")
        
        logger.info(f"Plants: {model_data.plants}")
        logger.info(f"Number of plants: {len(model_data.plants)}")
        
        logger.info(f"Time blocks: {model_data.time_blocks}")
        logger.info(f"Number of time blocks: {len(model_data.time_blocks)}")
        
        logger.info(f"Technologies: {model_data.technologies}")
        logger.info(f"Number of technologies: {len(model_data.technologies)}")
        
        logger.info("Scenarios:")
        for scenario, value in model_data.scenarios.items():
            status = "Active" if value == 1 else "Inactive"
            logger.info(f"- {scenario}: {status}")
        
        logger.info("Price Scenarios:")
        for scenario, value in model_data.price_scenarios.items():
            status = "Active" if value == 1 else "Inactive"
            logger.info(f"- {scenario}: {status}")
        
        logger.info("Plant Data Preview:")
        logger.info(f"Shape: {model_data.gen_data.shape}")
        
        logger.info("Price Generation Data Preview:")
        logger.info(f"Shape: {model_data.price_gen.shape}")
        
        logger.info("Price Distribution Preview:")
        logger.info(f"Shape: {model_data.price_dist.shape}")
        
        logger.info("Price Duration Preview:")
        logger.info(f"Shape: {model_data.price_dur.shape}")
        
        logger.info("FC PPA Data Preview:")
        logger.info(f"Shape: {model_data.fc_ppa.shape}")
        
        logger.info("Other Data Preview:")
        logger.info(f"Shape: {model_data.other.shape}")
        
        logger.info("Technology Parameters Preview:")
        logger.info(f"Shape: {model_data.tech_params.shape}")
        
        # Check for any missing values
        logger.info("\n" + "=" * 60)
        logger.info("MISSING VALUES CHECK")
        logger.info("=" * 60)
        
        for attr_name, df in {
            'gen_data': model_data.gen_data,
            'price_gen': model_data.price_gen,
            'price_dist': model_data.price_dist,
            'price_dur': model_data.price_dur,
            'fc_ppa': model_data.fc_ppa,
            'other': model_data.other,
            'tech_params': model_data.tech_params
        }.items():
            if not df.empty:
                missing = df.isnull().sum().sum()
                logger.info(f"{attr_name}: {missing} missing values")
            else:
                logger.info(f"{attr_name}: Empty DataFrame")
        
        # Detailed check for NaN values in each dataframe
        logger.info("\n" + "=" * 60)
        logger.info("DETAILED NaN VALUE ANALYSIS")
        logger.info("=" * 60)
        
        for attr_name, df in {
            'gen_data': model_data.gen_data,
            'price_gen': model_data.price_gen, 
            'price_dist': model_data.price_dist,
            'price_dur': model_data.price_dur,
            'fc_ppa': model_data.fc_ppa,
            'other': model_data.other,
            'tech_params': model_data.tech_params
        }.items():
            if df.empty:
                logger.info(f"\n{attr_name}: Empty DataFrame")
                continue
                
            logger.info(f"\nChecking {attr_name}:")
            # Get columns with NaN values and their counts
            nan_cols = df.isna().sum()
            nan_cols = nan_cols[nan_cols > 0]  # Only show columns with NaNs
            
            if len(nan_cols) > 0:
                logger.info("Columns containing NaN values:")
                for col, count in nan_cols.items():
                    logger.info(f"  - {col}: {count} NaN values")
            else:
                logger.info("No NaN values found")
                
        logger.info("\n" + "=" * 60)
        logger.info("DATA LOADING COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in data initialization: {str(e)}")
        raise