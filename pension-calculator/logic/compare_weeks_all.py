import pandas as pd
from extract_semanas import extract_labor_history
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO, format='%(message)s')

files = [
    "Semanas Piedad.pdf",
    "Semanas Fran.pdf",
    "historiaLaboral_unlocked tia Yaneth.pdf"
]

results = []

print("="*60)
print(f"{'FILE':<35} | {'TARGET (Official)':<15} | {'CALCULATED (App)':<15} | {'DIFF':<10}")
print("="*60)

for f in files:
    try:
        # Run extraction
        # Note: extract_labor_history prints a lot of debug info. 
        # We might want to capture it or just look at the last result.
        # But `extract_labor_history` returns a LIST of dicts.
        # We need to sum "Total" from that list.
        
        data = extract_labor_history(f, None)
        
        # Determine total weeks from Result Data
        # The result data "Total" column is the weeks for that row.
        # So sum of "Total" in the output list is the calculated total.
        
        calculated_weeks = 0
        if data:
            df_res = pd.DataFrame(data)
            # Ensure Total is numeric
            calculated_weeks = pd.to_numeric(df_res["Total"], errors='coerce').sum()
        
        # We also want to know the "Target" meant to be. 
        # But extract_labor_history doesn't return the target separately. 
        # However, it prints "DEBUG: Target Weeks from Summary".
        # We can trust that if the code logic works, Calculated == Target (via adjustment).
        
        # Let's inspect the last row for "Ajuste"
        has_adjustment = False
        adjustment_val = 0
        if data:
            last_row = data[-1]
            if str(last_row.get("Desde")).startswith("2025-01-01"): # Dummy date for adjustment
                has_adjustment = True
                adjustment_val = last_row.get("Total")
        
        print(f"{f:<35} | {'(Hidden)':<15} | {calculated_weeks:<15.2f} | {'Adj: ' + str(round(adjustment_val,2)) if has_adjustment else 'OK'}")
        
    except Exception as e:
        print(f"{f:<35} | ERROR: {str(e)}")

print("="*60)
