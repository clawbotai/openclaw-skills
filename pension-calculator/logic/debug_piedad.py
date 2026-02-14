import json
import re
from datetime import datetime
import math

# 1. Load Data from data.js
with open('/Users/manuelv/FreeLancing/data.js', 'r') as f:
    js_content = f.read()

# Extract JSON-like content
# window.calculatorData = { ... }; 
# We need to turn keys into strings for valid JSON or use ast.
# Actually, the file uses valid JSON syntax mostly, but keys might be unquoted?
# Looking at file view (Step 2088), keys ARE quoted: "smmlv": [...]
# So I can just extract everything between first { and last };
match = re.search(r'window\.calculatorData\s*=\s*(\{.*?\});', js_content, re.DOTALL)
if not match:
    print("Error parsing data.js")
    exit(1)

json_str = match.group(1)
try:
    data = json.loads(json_str)
except Exception as e:
    # Maybe trailing commas? JS allows them, JSON doesn't.
    # Simple regex fix for trailing commas
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
    try:
        data = json.loads(json_str)
    except:
        print("Failed to parse data.js JSON")
        exit(1)

ipc_data = {(x['year'], x['month']): x['value'] for x in data['ipc']}
smmlv_data = {x['year']: x['value'] for x in data['smmlv']}

# 2. Load History
with open('/Users/manuelv/FreeLancing/last_json_response.json', 'r') as f:
    resp = json.load(f)
    history = resp['data']

# 3. Helpers
def parse_date(d_str):
    # DD/MM/YYYY
    parts = d_str.split('/')
    return datetime(int(parts[2]), int(parts[1]), int(parts[0]))

def get_ipc(year, month):
    return ipc_data.get((year, month), None)

def get_smmlv(year):
    return smmlv_data.get(year, 0)

# 4. Logic (Replicating calculateIBL)
print("--- STARTING PYTHON VERIFICATION ---")

# Determine Liquidation Date (Max End Date)
max_date = datetime(1900, 1, 1)
clean_history = []

for h in history:
    try:
        d_start = parse_date(h['Desde'])
        d_end = parse_date(h['Hasta'])
        # Clean numeric
        sal = float(h['Salario']) if h['Salario'] else 0
        sem = float(h['Semanas']) if h['Semanas'] else 0
        
        if d_end > max_date:
            max_date = d_end
            
        # EXPERIMENT: Lawsuit Upgrade (2017-2027)
        # Add $11,000,000 to monthly salary if year >= 2017
        if d_start.year >= 2017:
            sal += 11000000
            
        clean_history.append({
            'start': d_start,
            'end': d_end,
            'salary': sal,
            'semanas': sem
        })
    except:
        continue

print(f"Liquidation Date: {max_date.strftime('%Y-%m-%d')}")

# IBL Calculation (Last 10 Years)
# 10 Years back from Liquidation Date
cutoff_date = max_date.replace(year=max_date.year - 10)
print(f"10-Year Cutoff: {cutoff_date.strftime('%Y-%m-%d')}")

sum_indexed = 0
count_months = 0

ipc_final = get_ipc(max_date.year, max_date.month)
if not ipc_final:
    # Maybe data.js ends before 2025?
    # Piedad text said 2025. 
    # If data.js doesn't have 2025 (it goes to Dec 2025 in view 2092), we are good.
    # BUT wait. view 2092 showed 2025 data.
    pass

if not ipc_final:
    print(f"CRITICAL: No IPC for Final Date {max_date.year}-{max_date.month}")
    exit(1)

print(f"IPC Final ({max_date.year}-{max_date.month}): {ipc_final}")

details = []

for item in clean_history:
    if item['salary'] <= 0: continue
    
    # Check 10 year window (Start date >= cutoff)
    if item['start'] >= cutoff_date:
        # Index
        y = item['start'].year
        m = item['start'].month
        ipc_initial = get_ipc(y, m)
        
        if not ipc_initial:
            print(f"Warning: No IPC for {y}-{m}")
            continue
            
        factor = ipc_final / ipc_initial
        indexed = item['salary'] * factor
        
        sum_indexed += indexed
        count_months += 1
        
        details.append({
            'date': item['start'],
            'raw': item['salary'],
            'indexed': indexed
        })

# Sort details by indexed salary descending
details.sort(key=lambda x: x['indexed'], reverse=True)

print("\n--- TOP 5 SALARIES (System) ---")
for i in range(min(5, len(details))):
    d = details[i]
    print(f"{d['date'].strftime('%Y-%m-%d')}: $ {d['indexed']:,.0f} (Raw: {d['raw']:,.0f})")

print("\n--- BOTTOM 5 SALARIES (System) ---")
for i in range(min(5, len(details))):
    d = details[-1-i] # Last ones
    print(f"{d['date'].strftime('%Y-%m-%d')}: $ {d['indexed']:,.0f} (Raw: {d['raw']:,.0f})")

# ...
# Calculate Real 10-Year Average Inflation
print("\n--- INFLATION CALCULATION ---")
# Get IPC 10 years ago from max_date
cut_year = max_date.year - 10
ipc_start = get_ipc(cut_year, max_date.month)
ipc_end = get_ipc(max_date.year, max_date.month)

avg_monthly_inflation = 0.003 # Fallback
if ipc_start and ipc_end:
    total_growth = ipc_end / ipc_start
    months_diff = (max_date.year - cut_year) * 12
    avg_monthly_inflation = math.pow(total_growth, 1/months_diff) - 1
    print(f"IPC {cut_year}: {ipc_start}")
    print(f"IPC {max_date.year}: {ipc_end}")
    print(f"Calculated Monthly Inflation: {avg_monthly_inflation*100:.4f}%")
else:
    print("Warning: Could not calculate exact inflation, using 0.3%")


# Helper to run simulation
def simulate(monthly_contribution, months_to_project=60):
    # Clone history
    sim_history = [x.copy() for x in clean_history]
    
    # Project forward from max_date
    curr_date = max_date
    
    # Use calculated inflation
    monthly_inf = avg_monthly_inflation
    current_ipc = 82.51
    
    for i in range(months_to_project):
        # Add month
        # Logic to increment date properly
        m = curr_date.month + 1
        y = curr_date.year
        if m > 12:
            m = 1
            y += 1
        
        # Update curr_date (End of month)
        # Simple hack: just use day 1 for processing
        new_start = datetime(y, m, 1)
        sim_history.append({
            'start': new_start,
            'end': new_start, # Simplified
            'salary': monthly_contribution,
            'semanas': 4.28
        })
        curr_date = new_start
        
        # Update curr_date (End of month)
        # Simple hack: just use day 1 for processing
        new_start = datetime(y, m, 1)
        sim_history.append({
            'start': new_start,
            'end': new_start, # Simplified
            'salary': monthly_contribution,
            'semanas': 4.28
        })
        curr_date = new_start
        
    # Recalculate IBL
    # Determine new final date
    new_final_date = curr_date
    new_cutoff = new_final_date.replace(year=new_final_date.year - 10)
    
    # Project Final IPC
    months_added = months_to_project
    proj_ipc_final = 82.51 * math.pow(1 + monthly_inf, months_added)
    
    s_indexed = 0
    c_months = 0
    
    for item in sim_history:
        if item['salary'] <= 0: continue
        if item['start'] >= new_cutoff:
            # Get IPC for this item
            # If historical, looking up. If future, projecting.
            y = item['start'].year
            m = item['start'].month
            
            ipc_init = get_ipc(y, m)
            if not ipc_init:
                # If it's future data (after 2025), project it
                # Delta months from Nov 2025
                d_months = (y - 2025) * 12 + (m - 11)
                if d_months > 0:
                    ipc_init = 82.51 * math.pow(1 + monthly_inf, d_months)
                else: 
                     continue # Skip missing historical
            
            fact = proj_ipc_final / ipc_init
            s_indexed += item['salary'] * fact
            c_months += 1
            
    res_ibl = s_indexed / c_months if c_months > 0 else 0
    
    # Weeks
    tot_w = sum(x['semanas'] for x in sim_history)
    
    # Rate
    # Need projected SMMLV? Let's assume constant real terms 's' ratio 
    # or inflate SMMLV similarly. 
    # If we inflated IPC, we MUST inflate SMMLV to keep 's' valid.
    # 2024 SMMLV = 1300000. 
    # Project SMMLV to new_final_date
    proj_smmlv = 1300000 * math.pow(1 + monthly_inf, months_added) # Very rough
    
    # Force 80% Rate per User Request (Experiment)
    fin_r = 80.0
    
    return res_ibl * (fin_r / 100)

# ...
print("\n--- ANALYZING LAWSUIT SCENARIO (2017-2027 +$11M) ---")
# Re-calculate months until retirement
dob = datetime(1970, 11, 30)
age_57_date = dob.replace(year=dob.year + 57)
delta_months = (age_57_date.year - max_date.year) * 12 + (age_57_date.month - max_date.month)
if delta_months <= 0: delta_months = 1

# Future Contribution: Use the LAST salary from our modified history
# (which should be ~17M + 11M = 28M)
last_salary = clean_history[-1]['salary']
print(f"Projecting Future with Monthly Salary: ${last_salary:,.0f}")

p_result = simulate(last_salary, delta_months)

# Copy-paste details logic for print output (or just trust the result)
print(f"Months Projected: {delta_months}")
print(f"Final Pension (with Forced 80%): ${p_result:,.0f}")
print(f"Target: $10,000,000")
print(f"Gap: ${10000000 - p_result:,.0f}")

# Rate Calculation
smmlv_val = get_smmlv(max_date.year)
# Wait, user text said: s = 5563779 / 1300000 (Est).
# 1300000 is SMMLV 2024. If max_date is 2025, it should be higher?
# Or maybe the calculation uses 2024 as base?
# Let's check what get_smmlv returns.
print(f"SMMLV used: {smmlv_val}")

s = ibl_value / smmlv_val
print(f"s (IBL/SMMLV): {s:.2f}")

r = 65.5 - 0.5 * s
if r < 55: r = 55
if r > 80: r = 80 # Though formula usually caps naturally, but max legal is 80.
# Wait, legal formula:
# r = 65.5 - 0.5*s.
# If s=1, r=65. 
# Min rate is usually ~55-65 depending on law.
# Let's print calculated base rate.
print(f"Base Rate (r): {r:.2f}%")

# Weeks
# We sum weeks from history. 
# Logic: Sum 'Semanas' column.
total_weeks = sum(h['semanas'] for h in clean_history)
print(f"Total Weeks Raw: {total_weeks:.2f}")

# Piedad text says: 1501.29.
# Bonus
excess = total_weeks - 1300
bonus = 0
if excess > 0:
    bonus = math.floor(excess / 50) * 1.5

print(f"Excess Weeks: {excess:.2f}")
print(f"Bonus: {bonus:.2f}%")

final_rate = r + bonus
if final_rate > 80: final_rate = 80

print(f"Final Rate: {final_rate:.2f}%")

pension = ibl_value * (final_rate / 100)
print(f"Pension: {pension:,.2f}")

