import pandas as pd

# === Load Excel ===
file_path = "Coal_RR_allocation.xlsx"

rr_input = pd.read_excel(file_path, sheet_name="Input_RR")
allocation = pd.read_excel(file_path, sheet_name="Allocation")
gen_profile = pd.read_excel(file_path, sheet_name="Generation_Profile")

# === Clean generation profile ===
gen_profile = gen_profile.rename(columns={
    "Unnamed: 0": "Year",
    "Unnamed: 1": "Tariff",  # USD/MWh
    "Total Coal Generation Predicted by IEA (TWh)": "BAU_TWh",
    "Unnamed: 3": "AD_TWh"
})

# Convert TWh → MWh (1 TWh = 1,000,000 MWh)
gen_profile["BAU_MWh"] = pd.to_numeric(gen_profile["BAU_TWh"], errors="coerce") * 1_000_000
gen_profile["AD_MWh"]  = pd.to_numeric(gen_profile["AD_TWh"], errors="coerce") * 1_000_000

# Drop NaNs
gen_profile = gen_profile.dropna(subset=["Year"])

# === System-level stranded cost ===
results = pd.merge(rr_input, gen_profile[["Year", "Tariff", "BAU_MWh", "AD_MWh"]], on="Year", how="inner")

# RR_coal is in million USD, so scale revenues into million USD
for scenario in ["BAU", "AD"]:
    results[f"Revenue_{scenario}"] = (results["Tariff"] * results[f"{scenario}_MWh"]) / 1_000_000
    results[f"Gap_{scenario}"] = results["RR_coal"] - results[f"Revenue_{scenario}"]

# === Plant-level stranded cost allocation ===
# Use allocation shares
plant_cols = [c for c in allocation.columns if c not in ["Year", "RR_coal", "Total_allocated"]]
allocation_long = allocation.melt(id_vars=["Year"], value_vars=plant_cols,
                                  var_name="Plant", value_name="RR_alloc")

# Merge with system gaps
plant_sc = allocation_long.merge(results[["Year", "Gap_BAU", "Gap_AD"]], on="Year")

# Allocate stranded cost proportionally to RR_alloc
for scenario in ["BAU", "AD"]:
    plant_sc[f"Stranded_{scenario}"] = (
        plant_sc["RR_alloc"] / plant_sc.groupby("Year")["RR_alloc"].transform("sum")
    ) * plant_sc[f"Gap_{scenario}"]

# === Save outputs ===
results.to_excel("System_Stranded_Cost.xlsx", index=False)
plant_sc.to_excel("Plant_Stranded_Cost.xlsx", index=False)

print("System-level results saved to System_Stranded_Cost.xlsx")
print("Plant-level results saved to Plant_Stranded_Cost.xlsx")
