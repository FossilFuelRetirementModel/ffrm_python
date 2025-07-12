# Intermediate Decarbonization Scenarios

## Overview

This feature adds support for intermediate decarbonization scenarios between the Business-as-Usual (BAU) and Accelerated Decarbonization (AD) scenarios. This allows for more granular analysis of different decarbonization pathways.

## New Scenarios

Three intermediate scenarios have been added:

- **AD_25**: 25% of the way from BAU to AD (1/4 AD)
- **AD_50**: 50% of the way from BAU to AD (1/2 AD)  
- **AD_75**: 75% of the way from BAU to AD (3/4 AD)

## How It Works

The intermediate scenarios are generated using linear interpolation between BAU and AD generation targets:

```
Intermediate_Value = BAU_Value + Interpolation_Factor × (AD_Value - BAU_Value)
```

Where:
- `Interpolation_Factor` is 0.25, 0.50, or 0.75 for AD_25, AD_50, and AD_75 respectively
- `BAU_Value` and `AD_Value` are the generation targets for each year

## Usage

### Command Line Interface

You can now specify intermediate scenarios in the command line:

```bash
# Run all scenarios including intermediate ones
python model.py --scenarios BAU AD AD_25 AD_50 AD_75

# Run only intermediate scenarios
python model.py --scenarios AD_25 AD_50 AD_75

# Run specific intermediate scenario with price scenarios
python model.py --scenarios AD_50 --price-scenarios MarketPrice AvgPPAPrice
```

### Available Scenarios

The following scenarios are now available:
- `BAU` - Business as Usual
- `AD` - Accelerated Decarbonization  
- `AD_25` - 25% decarbonization (1/4 AD)
- `AD_50` - 50% decarbonization (1/2 AD)
- `AD_75` - 75% decarbonization (3/4 AD)

## Implementation Details

### Configuration

The intermediate scenarios are defined in `config.py`:

```python
INTERMEDIATE_SCENARIOS = {
    'AD_25': 0.25,   # 25% of the way from BAU to AD
    'AD_50': 0.50,   # 50% of the way from BAU to AD
    'AD_75': 0.75    # 75% of the way from BAU to AD
}
```

### Function

The `generate_intermediate_scenarios()` function in `energy_data_processor.py`:

1. Loads the original BAU and AD generation targets
2. Calculates intermediate values using linear interpolation
3. Adds the new scenarios to the price_gen DataFrame
4. Returns updated ModelData with all scenarios

### Model Behavior

For intermediate scenarios:
- **Capacity**: Uses variable capacity (like AD scenario)
- **Generation Targets**: Uses interpolated values between BAU and AD
- **Constraints**: Same as AD scenario (allows capacity changes)

## Testing

Run the test script to verify the functionality:

```bash
python test_intermediate_scenarios.py
```

This will:
1. Load the data
2. Generate intermediate scenarios
3. Display the results
4. Verify the interpolation calculations

## Example Output

```
Generating AD_25 scenario (interpolation factor: 0.25)
  Year 2021: BAU=100.00, AD=80.00, AD_25=95.00
  Year 2022: BAU=98.00, AD=75.00, AD_25=90.75
  ...

Generating AD_50 scenario (interpolation factor: 0.50)
  Year 2021: BAU=100.00, AD=80.00, AD_50=90.00
  Year 2022: BAU=98.00, AD=75.00, AD_50=86.50
  ...

Generating AD_75 scenario (interpolation factor: 0.75)
  Year 2021: BAU=100.00, AD=80.00, AD_75=85.00
  Year 2022: BAU=98.00, AD=75.00, AD_75=82.25
  ...
```