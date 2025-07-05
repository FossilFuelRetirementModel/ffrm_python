
import pandas as pd

# Load Excel input
input_file = "debt_input_with_retirement.xlsx"
debt_df = pd.read_excel(input_file, sheet_name="DebtStructure")
retirement_df = pd.read_excel(input_file, sheet_name="RetirementSchedule")

# Merge both sheets
df = pd.merge(debt_df, retirement_df, on="Plant Name")

# Initialize result container
results = []

# Loop over each plant
for _, row in df.iterrows():
    plant = row["Plant Name"]
    start_year = int(row["Loan Start Year"])
    loan_amount = row["Loan Amount (USD million)"]
    term = int(row["Loan Term (years)"])
    rate = row["Interest Rate (%)"] / 100
    repayment_type = row["Repayment Type"]
    end_year = start_year + term - 1

    # Create amortization schedule
    principal_annual = loan_amount / term
    debt_schedule = []
    remaining_principal = loan_amount

    for year in range(start_year, start_year + term):
        interest_payment = remaining_principal * rate
        total_payment = principal_annual + interest_payment
        remaining_principal -= principal_annual
        debt_schedule.append({
            "Year": year,
            "Remaining Principal": max(0, remaining_principal)
        })

    debt_df_schedule = pd.DataFrame(debt_schedule)

    # Determine stranded debt under each scenario
    for scenario in ["BAU", "NZ"]:
        retire_year = int(row[f"Retirement Year ({scenario})"])
        stranded_debt = debt_df_schedule[debt_df_schedule["Year"] >= retire_year]["Remaining Principal"].sum()
        results.append({
            "Plant Name": plant,
            "Scenario": scenario,
            "Retirement Year": retire_year,
            "Stranded Debt (USD million)": stranded_debt
        })

# Output results
results_df = pd.DataFrame(results)
print("=== Stranded Debt Summary ===")
print(results_df.to_string(index=False))
