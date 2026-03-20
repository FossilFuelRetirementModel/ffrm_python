import pandas as pd
import numpy as np

# === Input loan data ===
data = [
    {"plant": "Medupi", "loan": 1537.78, "rate": 0.0575, "term": 15, "grace": 5, "start_year": 2017},
    {"plant": "Kusile", "loan": 2700.00, "rate": 0.0575, "term": 15, "grace": 5, "start_year": 2018},
]

df = pd.DataFrame(data)

# === Parameters ===
retire_year_nz = 2050   # Net Zero scenario retirement
base_year = 2024        # Analysis starts

# === Function to calculate outstanding debt ===
def calc_stranded_debt(row, retire_year):
    start = row["start_year"]
    term = row["term"]
    grace = row["grace"]
    principal = row["loan"]

    # Equal Principal Payment schedule
    repayment_years = list(range(start + grace, start + term + 1))
    repayment = principal / (term - grace) if term > grace else principal

    # Track outstanding debt
    outstanding = principal
    for y in repayment_years:
        if y >= retire_year:  # retirement before loan maturity
            return outstanding
        outstanding -= repayment
    return 0.0

# === Apply function ===
df["stranded_debt"] = df.apply(lambda r: calc_stranded_debt(r, retire_year_nz), axis=1)

# === Convert to USD Millions ===
df["stranded_debt_million"] = df["stranded_debt"]

# === Results ===
print("\n=== Stranded Debt (if retired in 2050) ===")
for _, row in df.iterrows():
    print(f"{row['plant']:<10} : {row['stranded_debt_million']:.2f} Million USD")

system_total = df["stranded_debt_million"].sum()
print(f"\n System Total Stranded Debt: {system_total:.2f} Million USD")

# === Export ===
df.to_excel("Stranded_Debt_Results.xlsx", index=False)
 