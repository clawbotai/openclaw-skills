import pandas as pd
import datetime
import json
import re

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

# Target IPC (Liquidation Date)
# Using latest known date (e.g. Dec 2024 or 2025 if projected)
# For accurate "Current Value", we index to the "End of Plan" or "Today"?
# Usually "Today's Pension" is calculated at Today's Value.
# So we index to the latest IPC available in the system.
LATEST_IPC_DATE = sorted(ipc_map.keys())[-1]
LATEST_IPC_VAL = ipc_map[LATEST_IPC_DATE]

# Load Boosted History
df = pd.read_excel('piedad_boosted.xlsx')

def parse_date(val):
    if pd.isna(val): return None
    s = str(val).strip()
    try: return pd.to_datetime(s)
    except: return None

# Bucket by Year
yearly_nom_sum = {}
yearly_idx_sum = {}
yearly_count = {}

for _, row in df.iterrows():
    s = parse_date(row['Desde'])
    e = parse_date(row['Hasta'])
    val = float(row['Salario'])
    
    if not s or not e: continue
    
    # Iterate months
    curr = datetime.datetime(s.year, s.month, 1)
    while curr <= e:
        y = curr.year
        if y >= 2017:
            # Nominal
            yearly_nom_sum[y] = yearly_nom_sum.get(y, 0) + val
            
            # Indexed
            ipc_curr = get_ipc(curr.year, curr.month)
            factor = LATEST_IPC_VAL / ipc_curr
            indexed_val = val * factor
            yearly_idx_sum[y] = yearly_idx_sum.get(y, 0) + indexed_val
            
            yearly_count[y] = yearly_count.get(y, 0) + 1
        curr = (curr.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

# Future Projection (3 Years Scenario: ~$15.6M)
FUTURE_IBC = 15_670_885
FUTURE_YEARS = [2025, 2026, 2027]

print(f"{'Year':^6} | {'Avg. Nominal IBL':^20} | {'Avg. Indexed IBL':^20} | {'Status':^15}")
print("-" * 75)

# Historical
for y in sorted(yearly_nom_sum.keys()):
    avg_nom = yearly_nom_sum[y] / yearly_count[y]
    avg_idx = yearly_idx_sum[y] / yearly_count[y]
    print(f"{y:^6} | ${avg_nom:^18,.0f} | ${avg_idx:^18,.0f} | {'Historical':^15}")

# Future (Assumed Constant Value - Index Factor 1.0)
for y in FUTURE_YEARS:
    # Future money is technically "Nominal = Indexed" if we project in Constant Pesos
    print(f"{y:^6} | ${FUTURE_IBC:^18,.0f} | ${FUTURE_IBC:^18,.0f} | {'Projected':^15}")
