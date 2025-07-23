#!/usr/bin/env python3
"""
Test script for intermediate scenario generation functionality.

This script demonstrates how to generate intermediate decarbonization scenarios
between BAU (Business as Usual) and AD (Accelerated Decarbonization).
"""

import pandas as pd
from pathlib import Path
from config import Config
from energy_data_processor import load_excel_data, initialize_model_data, generate_intermediate_scenarios

def test_intermediate_scenarios():
    """
    Test the intermediate scenario generation functionality.
    """
    print("=" * 60)
    print("TESTING INTERMEDIATE SCENARIO GENERATION")
    print("=" * 60)
    
    try:
        # Load data
        print("\n1. Loading Excel data...")
        file_path = Path(Config.INPUT_FILE)
        if not file_path.exists():
            print(f"ERROR: Input file not found: {file_path}")
            return
        
        data = load_excel_data(file_path)
        model_data = initialize_model_data(data)
        
        print(f"✓ Loaded data with {len(model_data.years)} years")
        print(f"✓ Original scenarios: {list(model_data.scenarios.keys())}")
        
        # Show original BAU and AD values
        print("\n2. Original BAU and AD generation targets:")
        print("-" * 50)
        for year in model_data.years[:5]:  # Show first 5 years
            bau_value = model_data.price_gen.loc[year, 'BAU']
            ad_value = model_data.price_gen.loc[year, 'AD']
            print(f"Year {year}: BAU={bau_value:.2f} TWh, AD={ad_value:.2f} TWh")
        
        # Generate intermediate scenarios
        print("\n3. Generating intermediate scenarios...")
        print("-" * 50)
        updated_model_data = generate_intermediate_scenarios(model_data)
        
        # Show results
        print("\n4. Generated intermediate scenarios:")
        print("-" * 50)
        for year in model_data.years[:5]:  # Show first 5 years
            bau_value = updated_model_data.price_gen.loc[year, 'BAU']
            ad_value = updated_model_data.price_gen.loc[year, 'AD']
            ad_25_value = updated_model_data.price_gen.loc[year, 'AD_25']
            ad_50_value = updated_model_data.price_gen.loc[year, 'AD_50']
            ad_75_value = updated_model_data.price_gen.loc[year, 'AD_75']
            
            print(f"Year {year}:")
            print(f"  BAU:   {bau_value:.2f} TWh")
            print(f"  AD_25: {ad_25_value:.2f} TWh (25% of BAU→AD)")
            print(f"  AD_50: {ad_50_value:.2f} TWh (50% of BAU→AD)")
            print(f"  AD_75: {ad_75_value:.2f} TWh (75% of BAU→AD)")
            print(f"  AD:    {ad_value:.2f} TWh")
            print()
        
        # Verify interpolation
        print("5. Verifying interpolation calculations:")
        print("-" * 50)
        year = model_data.years[0]
        bau_value = updated_model_data.price_gen.loc[year, 'BAU']
        ad_value = updated_model_data.price_gen.loc[year, 'AD']
        ad_25_value = updated_model_data.price_gen.loc[year, 'AD_25']
        ad_50_value = updated_model_data.price_gen.loc[year, 'AD_50']
        ad_75_value = updated_model_data.price_gen.loc[year, 'AD_75']
        
        # Calculate expected values
        expected_ad_25 = bau_value + 0.25 * (ad_value - bau_value)
        expected_ad_50 = bau_value + 0.50 * (ad_value - bau_value)
        expected_ad_75 = bau_value + 0.75 * (ad_value - bau_value)
        
        print(f"Year {year} verification:")
        print(f"  AD_25: Expected={expected_ad_25:.2f}, Actual={ad_25_value:.2f}, Match={abs(expected_ad_25 - ad_25_value) < 0.01}")
        print(f"  AD_50: Expected={expected_ad_50:.2f}, Actual={ad_50_value:.2f}, Match={abs(expected_ad_50 - ad_50_value) < 0.01}")
        print(f"  AD_75: Expected={expected_ad_75:.2f}, Actual={ad_75_value:.2f}, Match={abs(expected_ad_75 - ad_75_value) < 0.01}")
        
        print("\n" + "=" * 60)
        print("✓ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intermediate_scenarios() 