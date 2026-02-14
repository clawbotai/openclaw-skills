import pandas as pd
import datetime
import json
import re

# Goals
TARGET_PENSION = 10_000_000
SMMLV_2025 = 1_423_500
MAX_SALARY_LIMIT = 25 * SMMLV_2025

# Load Data
with open('data.js', 'r') as f:
    c = f.read()
    m = re.search(r'window\.calculatorData\s*=\s*(\{.*?\});', c, re.DOTALL)
    calc_data = json.loads(m.group(1))

ipc_map = {(i['year'], i['month']): i['value'] for i in calc_data['ipc']}
def get_ipc(y, m):
    # Fallback to latest known if future
    keys = sorted(ipc_map.keys())
    last_known = keys[-1]
    last_val = ipc_map[last_known]
    if (y, m) in ipc_map: return ipc_map[(y, m)]
    return last_val # Assume flat inflation for future purely for ratio calc or 

# We need the "Final IPC" for indexation. 
# Usually reliable to take the latest actual IPC.
# Future salaries are "Nominal" but effectively "Current Value" if we assume 0 inflation for simplicity 
# OR we perform everything in "Today's pesos".
# Let's assume the question implies "What Real Salary do I need to pay".
LATEST_IPC_VAL = get_ipc(2024, 12)

# Load History
df = pd.read_excel('piedad_boosted.xlsx')

def parse_date(val):
    if pd.isna(val): return None
    s = str(val).strip()
    if ' ' in s: s = s.split(' ')[0]
    # Handle DD/MM/YYYY
    if '/' in s: 
        p = s.split('/')
        if len(p) == 3: return datetime.datetime(int(p[2]), int(p[1]), int(p[0]))
    # Handle YYYY-MM-DD
    try: return pd.to_datetime(s)
    except: return None

# 1. Structure Current History into Monthly Map (Verified Logic)
monthly_map = {} 
hist_entries = []

for _, row in df.iterrows():
    s = parse_date(row['Desde'])
    e = parse_date(row['Hasta'])
    if not s or not e: continue
    
    val = float(row['Salario']) if not pd.isna(row['Salario']) else 0
    
    curr = datetime.datetime(s.year, s.month, 1)
    while curr <= e:
        k = curr.strftime("%Y-%m")
        if k not in monthly_map: monthly_map[k] = []
        monthly_map[k].append(val)
        curr = (curr.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

# Resolve overlaps (Max)
current_history = {}
for k, v in monthly_map.items():
    current_history[k] = max(v)

# Find last date in history
sorted_months = sorted(current_history.keys())
last_month_str = sorted_months[-1]
# E.g. "2025-03"

# 2. Simulation Function
def simulate_pension(future_salary, months_to_add=60): # 5 years projection?
    # Create a copy of history
    sim_history = current_history.copy()
    
    # Determine start date for future
    last_y, last_m = map(int, last_month_str.split('-'))
    curr_date = datetime.datetime(last_y, last_m, 1)
    
    start_future = curr_date + datetime.timedelta(days=32)
    start_future = start_future.replace(day=1)
    
    # Add future months
    for i in range(months_to_add):
        k = start_future.strftime("%Y-%m")
        sim_history[k] = future_salary
        start_future = (start_future.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        
    # Calculate Pension Params
    # A. Weeks
    # Count unique months * 4.28? Or use strict accounting.
    # Total Months roughly
    total_months_cnt = len(sim_history)
    weeks = total_months_cnt * 4.2857 
    # Current weeks from file is ~1800. 
    # Better to take base weeks + future weeks
    # Let's approximate base weeks = 1823 (verified earlier)
    # Plus (months_to_add * 4.28)
    base_weeks = 1823 
    # But wait, we might double count if we add to existing history?
    # The file has history up to 2025-03.
    # So base_weeks encompasses up to 2025-03.
    total_weeks = base_weeks + (months_to_add * 4.2857)
    
    # B. IBL (Last 10 Years from Validation Date)
    # Validation Date = start_future (end of projection)
    
    # Get last 120 months relative to END of projection
    all_keys = sorted(sim_history.keys(), reverse=True)
    ibl_window = all_keys[:120]
    
    sum_indexed = 0
    count = 0
    for k in ibl_window:
        y, m = map(int, k.split('-'))
        nominal = sim_history[k]
        ipc_val = get_ipc(y, m)
        
        # Assumption: Future Inflation matches Latest Known.
        # So Index Factor = 1.0 for future months.
        # For past months, Index Factor > 1.0
        factor = LATEST_IPC_VAL / ipc_val
        indexed = nominal * factor
        
        sum_indexed += indexed
        count += 1
        
    ibl = sum_indexed / 120 # Divisor 120 fixed
    
    # C. Rate
    s = ibl / SMMLV_2025
    r = 65.5 - (0.5 * s)
    
    # Bonus
    extra_weeks = total_weeks - 1300
    if extra_weeks > 0:
        blocks = int(extra_weeks // 50)
        r += (blocks * 1.5)
        
    if r > 80: r = 80
    
    # USER OVERRIDE: FORCE 80% RATE
    r = 80.0
    
    pension = ibl * (r/100)
    return pension, ibl, r, total_weeks

# 3. Solver
# We start simple. Assume we pay for X months.
# The user asked "pay ... from now on". This implies indefinite or "until retirement".
# Usually people want to know "If I pay X for the next 5 or 10 years".
# Or "What salary to hit 10M?".
# If IBL needed is > 25 SMMLV ($35M), it's impossible.
# Let's try to find Target Salary for varied durations (1, 3, 5, 10 years).

print(f"BASELINE STATUS (Up to {last_month_str}):")
p_base, ibl_base, r_base, w_base = simulate_pension(0, 0)
print(f"  Weeks: {w_base:.1f}")
print(f"  IBL: ${ibl_base:,.0f}")
print(f"  Pension: ${p_base:,.0f} (Rate: {r_base:.2f}%)")
print("-" * 50)

targets_years = [1, 2, 3, 5, 10]

print(f"{'Years Added':^12} | {'Req. Salary':^15} | {'Final Pension':^15} | {'Notes':^20}")
print("-" * 70)

for years in targets_years:
    months = years * 12
    
    # Binary Search for Salary
    low = SMMLV_2025
    high = 100_000_000 # 100M
    found = False
    
    for _ in range(20): # 20 iter sufficiency
        mid = (low + high) / 2
        p_res, _, _, _ = simulate_pension(mid, months)
        
        if abs(p_res - TARGET_PENSION) < 10000:
            low = mid
            found = True
            break
        elif p_res < TARGET_PENSION:
            low = mid
        else:
            high = mid
            
    res_sal = low
    final_p, final_ibl, final_r, final_w = simulate_pension(res_sal, months)
    
    note = ""
    if res_sal > MAX_SALARY_LIMIT:
        note = "EXCEEDS LEGAL CAP"
        res_sal = MAX_SALARY_LIMIT
        # Recalc max possible
        final_p, _, _, _ = simulate_pension(MAX_SALARY_LIMIT, months)
        
    print(f"{years:^12} | ${res_sal:^13,.0f} | ${final_p:^13,.0f} | {note:^20}")
    
