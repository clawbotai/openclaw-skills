import pandas as pd
import datetime
import json
import re

# Goals
TARGET_YEAR = 2027
SMMLV_2025 = 1_423_500
MAX_SALARY_LIMIT = 25 * SMMLV_2025

# User Defined Overrides (Monthly Average)
OVERRIDES = {
    2020: 9_655_833,
    2021: 9_993_786,
    2022: 11_000_000,
    2023: 12_760_000,
    2024: 14_300_000,
    2025: 15_653_000
}

# Load IPC Data
with open('data.js', 'r') as f:
    c = f.read()
    m = re.search(r'window\.calculatorData\s*=\s*(\{.*?\});', c, re.DOTALL)
    calc_data = json.loads(m.group(1))

ipc_map = {(i['year'], i['month']): i['value'] for i in calc_data['ipc']}
def get_ipc(y, m):
    keys = sorted(ipc_map.keys())
    last_known = keys[-1]
    if (y, m) in ipc_map: return ipc_map[(y, m)]
    return ipc_map[last_known]

LATEST_IPC_DATE = sorted(ipc_map.keys())[-1]
LATEST_IPC_VAL = ipc_map[LATEST_IPC_DATE]

# Load Original Data
# User said "based on the piedad file as is" -> original upload file
df = pd.read_excel('document for upload pension piedad.xlsx')

def parse_date(val):
    if pd.isna(val): return None
    s = str(val).strip()
    try: return pd.to_datetime(s)
    except: return None

# 1. Expand History to Months
monthly_data = {} # "YYYY-MM" -> val

for _, row in df.iterrows():
    s = parse_date(row['Desde'])
    e = parse_date(row['Hasta'])
    val = float(row['Salario'])
    
    if not s or not e: continue
    
    curr = datetime.datetime(s.year, s.month, 1)
    while curr <= e:
        y = curr.year
        # Store if not override later
        k = curr.strftime("%Y-%m")
        # For duplicates, take max (but we will override anyway for key years)
        current_max = monthly_data.get(k, 0)
        monthly_data[k] = max(current_max, val)
        curr = (curr.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

# 2. Apply Overrides (2020-2024)
# Iterate through all months of these years and set fixed value
for y in range(2020, 2025):
    target_val = OVERRIDES[y]
    for m in range(1, 13):
        k = f"{y}-{m:02d}"
        # We overwrite existing data or create if missing (assuming full year coverage requested)
        # "boost the 2020 monthly average" -> implies making it that value.
        monthly_data[k] = target_val

# 3. Project Future (2025, 2026, 2027)
# 2025 is in OVERRIDES
# 2026, 2027: User didn't specify, implies "rest stays the same" or continuation?
# "rest stays the same" usually refers to past.
# Context: "re calculate our final pension to 2027".
# I'll reflect the 2025 value ($15.6M) forward to 2026 and 2027.
future_val = OVERRIDES[2025]
for y in range(2025, 2028): # 2025, 2026, 2027
    val_to_use = OVERRIDES.get(y, future_val)
    for m in range(1, 13):
        k = f"{y}-{m:02d}"
        monthly_data[k] = val_to_use

# 4. Calculate Pension
# Liquidation Date: End of 2027
liq_date = datetime.datetime(2027, 12, 1)

# A. Weeks
# Count total unique months * 4.28
total_months = len(monthly_data)
weeks = total_months * 4.2857

# B. IBL (Last 10 Years: 2018-2027)
# Note: 2018-2019 are from Original File. 2020-2027 are Override/Projected.
last_10_years_months = []
curr = liq_date
for _ in range(120):
    k = curr.strftime("%Y-%m")
    if k in monthly_data:
        last_10_years_months.append((k, monthly_data[k]))
    else:
        # Gap? assume 0
        last_10_years_months.append((k, 0))
    # Go back one month
    # simplistic math:
    y, m = curr.year, curr.month
    if m == 1:
        curr = datetime.datetime(y-1, 12, 1)
    else:
        curr = datetime.datetime(y, m-1, 1)

sum_indexed = 0
for k, nom in last_10_years_months:
    y, m = map(int, k.split('-'))
    ipc_curr = get_ipc(y, m)
    factor = LATEST_IPC_VAL / ipc_curr
    sum_indexed += (nom * factor)

ibl = sum_indexed / 120

# C. Rate
s = ibl / SMMLV_2025
r = 65.5 - (0.5 * s)
extra_weeks = weeks - 1300
if extra_weeks > 0:
    blocks = int(extra_weeks // 50)
    r += (blocks * 1.5)
if r > 80: r = 80

pension = ibl * (r/100)

print(f"RESULTS FOR CUSTOM SCENARIO (Liquidation 2027):")
print("-" * 50)
print(f"Total Weeks: {weeks:,.1f}")
print(f"Final IBL (Indexed): ${ibl:,.0f}")
print(f"Replacement Rate: {r:.2f}%")
print(f"FINAL PENSION: ${pension:,.0f}")
print("-" * 50)
print(f"Yearly Breakdown (Nominal):")
for y in range(2018, 2028):
    # Avg for year
    sum_y = 0
    cnt_y = 0
    for m in range(1, 13):
        k = f"{y}-{m:02d}"
        if k in monthly_data:
            sum_y += monthly_data[k]
            cnt_y += 1
    avg = sum_y / cnt_y if cnt_y > 0 else 0
    print(f"  {y}: ${avg:,.0f}")
