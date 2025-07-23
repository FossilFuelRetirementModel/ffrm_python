import pandas as pd
from pathlib import Path
from config import Config
from typing import Dict, List
from dataclasses import dataclass
from pyomo.environ import *
@dataclass
class ModelData:
    """Class to hold all model data structures"""
    # Basic sets
    years: List[int]              # y: Years from 2021 to 2040
    plants: List[str]             # g: Plant identifiers (from coal_plant_data)
    time_blocks: List[str]        # t: Time blocks (from price_distribution)
    scenarios: Dict[str, int]     # s: BAU and AD scenarios
    price_scenarios: Dict[str, int]  # p: Market Price and PPA Price scenarios
    
    # Parameter data
    gen_data: pd.DataFrame        # GenData(g,*)  Plant-level data
    price_gen: pd.DataFrame       # Price_gen(y,*) Forecasted average price and total coal generation per year
    price_dist: pd.DataFrame      # Price_dist(y,t) Distribution of prices as multiple of average price
    price_dur: pd.DataFrame       # Price_dur(t,*) Duration of price blocks
    other: pd.DataFrame          # Other(*,*) Other parameters
    fc_ppa: pd.DataFrame         # FC_PPA(g,y) Mandatory capacity payment at 85% PLF for 25 years

def initialize_model_data(data: dict) -> ModelData:
    """
    Initialize model data structures from loaded Excel data
    
    Args:
        data: Dictionary containing DataFrames from Excel
    
    Returns:
        ModelData object containing all model structures
    """
    # Validate data for duplicate indices and remove nonsense indices like " " or nan (at the end)
    for key, df in data.items():
        if isinstance(df, pd.DataFrame):
            # Remove nonsense indices: empty strings or NaN at the end
            nonsense_indices = df.index[(df.index == " ") | (pd.isna(df.index))]
            if len(nonsense_indices) > 0:
                print(f"Removing nonsense indices from {key}: {list(nonsense_indices)}")
                df = df[~df.index.isin(nonsense_indices)]
                data[key] = df  # update in-place

            if df.index.duplicated().any():
                print(f"Warning: Duplicate indices found in {key}")
                print("Duplicate indices:", df.index[df.index.duplicated()].tolist())
                # Remove duplicates by keeping the first occurrence
                # data[key] = df[~df.index.duplicated(keep='first')]
    
    # print(data['price_distribution'])
    # print(data["price_dur"])
    # print(data['other'],data['fc_ppa'])
    print(data['coal_plant_data'],data['coal_plant_data'].index.tolist())
    
    return ModelData(
        years=Config.YEARS,
        plants=data['coal_plant_data'].index.tolist(),  # Assuming plant ID is index
        time_blocks=data['price_distribution'].columns.tolist(),   # Assuming time blocks are column names
        scenarios=Config.SCENARIOS,
        price_scenarios=Config.PRICE_SCENARIOS,
        
        # Data tables
        gen_data=data['coal_plant_data'],
        price_gen=data['price_gen'],
        price_dist=data['price_distribution'],
        price_dur=data['price_dur'],
        other=data['other'],
        fc_ppa=data['fc_ppa']
    )

def generate_intermediate_scenarios(model_data: ModelData) -> ModelData:
    """
    NEW: Generate intermediate decarbonization scenarios between BAU and AD.
    
    This function creates new generation targets for intermediate scenarios:
    - AD_25: 25% of the way from BAU to AD (1/4 AD)
    - AD_50: 50% of the way from BAU to AD (1/2 AD)
    - AD_75: 75% of the way from BAU to AD (3/4 AD)
    
    Args:
        model_data: Original model data with BAU and AD scenarios
        
    Returns:
        ModelData: Updated model data with intermediate scenarios added
    """
    try:
        # Create a copy of the price_gen DataFrame to avoid modifying the original
        extended_price_gen = model_data.price_gen.copy()
        
        # Get BAU and AD generation targets
        bau_targets = {}
        ad_targets = {}
        
        for year in model_data.years:
            if 'BAU' in model_data.price_gen.columns:
                bau_targets[year] = model_data.price_gen.loc[year, 'BAU']
            else:
                raise ValueError(f"BAU scenario not found in price_gen data for year {year}")
                
            if 'AD' in model_data.price_gen.columns:
                ad_targets[year] = model_data.price_gen.loc[year, 'AD']
            else:
                raise ValueError(f"AD scenario not found in price_gen data for year {year}")
        
        # Generate intermediate scenarios
        for scenario_name, interpolation_factor in Config.INTERMEDIATE_SCENARIOS.items():
            print(f"Generating {scenario_name} scenario (interpolation factor: {interpolation_factor})")
            
            for year in model_data.years:
                # Linear interpolation between BAU and AD
                bau_value = bau_targets[year]
                ad_value = ad_targets[year]
                
                # Calculate intermediate value: BAU + factor * (AD - BAU)
                intermediate_value = bau_value + interpolation_factor * (ad_value - bau_value)
                
                # Add to the DataFrame
                extended_price_gen.loc[year, scenario_name] = intermediate_value
                
                print(f"  Year {year}: BAU={bau_value:.2f}, AD={ad_value:.2f}, {scenario_name}={intermediate_value:.2f}")
        
        # Create updated scenarios dictionary including intermediate scenarios
        all_scenarios = {**Config.SCENARIOS, **Config.INTERMEDIATE_SCENARIOS}
        
        # Create new ModelData object with extended scenarios
        updated_model_data = ModelData(
            years=model_data.years,
            plants=model_data.plants,
            time_blocks=model_data.time_blocks,
            scenarios=all_scenarios,  # Include both original and intermediate scenarios
            price_scenarios=model_data.price_scenarios,
            
            # Data tables
            gen_data=model_data.gen_data,
            price_gen=extended_price_gen,  # Use extended price_gen
            price_dist=model_data.price_dist,
            price_dur=model_data.price_dur,
            other=model_data.other,
            fc_ppa=model_data.fc_ppa
        )
        
        print(f"\nSuccessfully generated intermediate scenarios: {list(Config.INTERMEDIATE_SCENARIOS.keys())}")
        return updated_model_data
        
    except Exception as e:
        print(f"Error generating intermediate scenarios: {str(e)}")
        raise

def load_excel_data(file_path: Path) -> dict:
    """Load all required data from Excel file"""
    try:
        # Read coal plant data
        coal_plant_data = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['COAL_PLANT'],
            **Config.EXCEL_CONFIG['CoalPlantData']
        )

        # Read price distribution data (includes time blocks and price duration)
        price_distribution = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['price_dist']
        )

        # Read time blocks (column headers from price distribution)
        time_blocks = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['time_blocks']
        )
        print("==============================================")
        print(time_blocks)
        # Read price duration
        price_duration = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_DIST'],
            **Config.EXCEL_CONFIG['Price_Distribution']['price_dur']
        )
        # print(price_duration)

        # Read price generation data
        price_gen = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['PRICE_GEN'],
            **Config.EXCEL_CONFIG['Price_Gen']
        )

        # Read other data
        other = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['OTHER'],
            **Config.EXCEL_CONFIG['Other']
        )

        # Read FC PPA data
        fc_ppa = pd.read_excel(
            file_path,
            sheet_name=Config.SHEETS['FC_PPA'],
            **Config.EXCEL_CONFIG['FC_PPA']
        )

        return {
            'coal_plant_data': coal_plant_data,
            'price_distribution': price_distribution,
            'time_blocks': time_blocks,
            'price_dur': price_duration,
            'price_gen': price_gen,
            'other': other,
            'fc_ppa': fc_ppa
        }

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise
    

if __name__ == "__main__":
    try:
        # Load Excel data
        raw_data = load_excel_data(Config.EXCEL_PATH)
        
        # Initialize model data structures
        model_data = initialize_model_data(raw_data)
        # Print key data for verification
        print("\n=== Model Data Overview ===")
        print(f"\nYears: {model_data.years}")
        print(f"Number of years: {len(model_data.years)}")
        
        print(f"\nPlants: {model_data.plants}")
        print(f"Number of plants: {len(model_data.plants)}")
        
        print(f"\nTime blocks: {model_data.time_blocks}")
        print(f"Number of time blocks: {len(model_data.time_blocks)}")
        
        print("\nScenarios:")
        for scenario, value in model_data.scenarios.items():
            print(f"- {scenario}: {'Active' if value == 1 else 'Inactive'}")
        
        print("\nPrice Scenarios:")
        for scenario, value in model_data.price_scenarios.items():
            print(f"- {scenario}: {'Active' if value == 1 else 'Inactive'}")
        
        print("\nGeneration Data Preview:")
        print(model_data.gen_data.head())
        print(f"Gen Data Shape: {model_data.gen_data.shape}")
        
        print("\nPrice Generation Data Preview:")
        print(model_data.price_gen.head())
        print(f"Price Gen Shape: {model_data.price_gen.shape}")
        
        print("\nPrice Distribution Preview:")
        print(model_data.price_dist.head())
        print(f"Price Distribution Shape: {model_data.price_dist.shape}")
        
        print("\nPrice Duration Preview:")
        # print(model_data.price_dur.head())
        print(model_data.price_dur['PercentTime']["Peak1"])        
        print(f"Price Duration Shape: {model_data.price_dur.shape}")
        
        print("\nFC PPA Data Preview:")
        print(model_data.fc_ppa.head())
        print(f"FC PPA Shape: {model_data.fc_ppa.shape}")
        
        print("\nOther Data Preview:")
        print(model_data.other.head())
        print(f"Other Data Shape: {model_data.other.shape}")
        
        # Check for any missing values
        print("\n=== Missing Values Check ===")
        for attr_name, df in {
            'gen_data': model_data.gen_data,
            'price_gen': model_data.price_gen,
            'price_dist': model_data.price_dist,
            'price_dur': model_data.price_dur,
            'fc_ppa': model_data.fc_ppa,
            'other': model_data.other
        }.items():
            missing = df.isnull().sum().sum()
            print(f"{attr_name}: {missing} missing values")
        
        # Detailed check for NaN values in each dataframe
        print("\n=== Detailed NaN Value Analysis ===")
        for attr_name, df in {
            'gen_data': model_data.gen_data,
            'price_gen': model_data.price_gen, 
            'price_dist': model_data.price_dist,
            'price_dur': model_data.price_dur,
            'fc_ppa': model_data.fc_ppa,
            'other': model_data.other
        }.items():
            print(f"\nChecking {attr_name}:")
            # Get columns with NaN values and their counts
            nan_cols = df.isna().sum()
            nan_cols = nan_cols[nan_cols > 0]  # Only show columns with NaNs
            
            if len(nan_cols) > 0:
                print("Columns containing NaN values:")
                for col, count in nan_cols.items():
                    print(f"  - {col}: {count} NaN values")
                    # Show rows with NaN values in this column
                    nan_rows = df[df[col].isna()]
                    if not nan_rows.empty:
                        print("    Rows with NaN values:")
                        print(nan_rows)
            else:
                print("No NaN values found")
    except Exception as e:
        print(f"Error in data initialization: {str(e)}")
        raise