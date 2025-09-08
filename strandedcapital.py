import pandas as pd
import matplotlib.pyplot as plt

# === User inputs ===
total_rab = 68270270270   # Total Regulatory Asset Base (USD)
cost_of_equity = 0.0815      # 8.15 % return
base_year = 2024             # Base year for discounting
nz_retire = 2050             # Net Zero retirement year
cf_bau_ret = 2051            # Counterfactual BAU retirement year

# === Load Allocation (RAB shares by station) ===
alloc = pd.read_excel("Coal_RR_allocation.xlsx", sheet_name="Allocation")
alloc.columns = alloc.columns.str.strip().str.lower()
plant_cols = [c for c in alloc.columns if c not in ["year", "rr_coal", "total_allocated"]]

# Convert wide to long
alloc_long = alloc.melt(id_vars=["year"], value_vars=plant_cols,
                        var_name="station", value_name="rr_alloc")

# Average allocation share across years
alloc_clean = alloc_long.groupby("station", as_index=False)["rr_alloc"].mean()

# Proper case names
alloc_clean["station"] = alloc_clean["station"].str.strip().str.capitalize()

# === Remove debt-funded plants ===
alloc_clean = alloc_clean[~alloc_clean["station"].isin(["Medupi", "Kusile"])]

# === Allocate RAB to stations ===
alloc_clean["rab_alloc"] = total_rab * alloc_clean["rr_alloc"] / alloc_clean["rr_alloc"].sum()
alloc_clean["annual_equity_return"] = alloc_clean["rab_alloc"] * cost_of_equity

# === Stranded equity (1 year foregone, discounted back to base year) ===
years_lost = cf_bau_ret - nz_retire   # = 1
discount_factor = (1 + cost_of_equity) ** (nz_retire - base_year)

alloc_clean["stranded_equity"] = alloc_clean["annual_equity_return"] * years_lost / discount_factor
alloc_clean["stranded_equity_million"] = alloc_clean["stranded_equity"] / 1e6  # USD Millions

# === Print results ===
print("\n=== Plant-level Stranded Equity (BAU=2051 vs NZ=2050, Equity-funded only) ===")
for _, row in alloc_clean.iterrows():
    print(f"{row['station']:<10} : {row['stranded_equity_million']:.2f} Million USD")

system_total = alloc_clean["stranded_equity_million"].sum()
print(f"\n  System Total Stranded Equity (Equity-funded plants only): {system_total:.2f} Million USD")

# === Save results ===
alloc_clean.to_excel("Stranded_Equity_Counterfactual.xlsx", index=False)

# === Plot plant-level bar chart ===
plt.figure(figsize=(12,6))
bars = plt.bar(alloc_clean["station"],
               alloc_clean["stranded_equity_million"],
               color="lightblue", edgecolor="black", linewidth=1.2)
plt.ylabel("Stranded Equity (Million USD)")
plt.title("State-Owned Stranded Equity per Power Plant")
plt.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.xticks(rotation=45, ha="right")
for bar in bars:
    h = bar.get_height()
    if h > 0:
        plt.text(bar.get_x()+bar.get_width()/2, h, f"{h:.0f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig("Stranded_Equity_Counterfactual_NoLoans.png", dpi=300)
plt.show()
