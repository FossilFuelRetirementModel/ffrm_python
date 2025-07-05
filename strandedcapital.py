
import pandas as pd

# Load Excel input file
excel_path = "stranded_capital_template.xlsx"
inputs = pd.read_excel(excel_path, sheet_name="Inputs", index_col="Parameter").squeeze()
generation = pd.read_excel(excel_path, sheet_name="Generation")
price = pd.read_excel(excel_path, sheet_name="Price")
cost = pd.read_excel(excel_path, sheet_name="Cost")

# Try to load future capex assumptions (optional sheet)
try:
    future_capex_df = pd.read_excel(excel_path, sheet_name="FutureCapex")
    has_future_capex = True
except:
    has_future_capex = False
    future_capex_df = pd.DataFrame(columns=["Year", "Capacity_MW", "Tech", "Capex_per_kW"])

# Extract parameters
discount_rate = inputs["DiscountRate"]
operational_life = int(inputs["OperationalLife"])
ownership_share = inputs["OwnershipShare"]
historical_capex_bau = inputs["Capex_BAU"]
historical_capex_css = inputs["Capex_CSS"]

# Merge data into one DataFrame
df = generation.merge(price, on="Year").merge(cost, on="Year")

# Calculate annual operating returns
df["Return_BAU"] = (df["Price ($/MWh)"] - df["Cost ($/MWh)"]) * df["Gen_BAU (GWh)"] * 1000
df["Return_CSS"] = (df["Price ($/MWh)"] - df["Cost ($/MWh)"]) * df["Gen_CSS (GWh)"] * 1000

# Filter for analysis years (e.g. 2022–2050)
start_year = 2022
end_year = 2050
df_filtered = df[df["Year"].between(start_year, end_year)].copy()
df_filtered = df_filtered.iloc[:operational_life]

# Calculate NPV of lost returns
df_filtered["Discount Factor"] = 1 / ((1 + discount_rate) ** (df_filtered["Year"] - start_year + 1))
df_filtered["NPV Difference"] = (df_filtered["Return_BAU"] - df_filtered["Return_CSS"]) * df_filtered["Discount Factor"]
npv_foregone_returns = df_filtered["NPV Difference"].sum()

# Calculate future capex if data is available
if has_future_capex and not future_capex_df.empty:
    future_capex_df["Capex_USD"] = future_capex_df["Capacity_MW"] * 1000 * future_capex_df["Capex_per_kW"] * ownership_share
    total_future_capex_bau = future_capex_df["Capex_USD"].sum()
else:
    total_future_capex_bau = 0

# Combine all capex
total_ec_bau = (historical_capex_bau * 1e6 * ownership_share) + total_future_capex_bau
total_ec_css = historical_capex_css * 1e6 * ownership_share  # typically zero

# Final stranded capital
stranded_capital = total_ec_bau - total_ec_css + npv_foregone_returns
print(f"Stranded Capital (with future investment): ${stranded_capital / 1e6:.2f} million USD")
