import pandas as pd
import datetime
import math
import json
import re

# Load data.js for IPC
with open('data.js', 'r') as f:
    c = f.read()
    m = re.search(r'window\.calculatorData\s*=\s*(\{.*?\});', c, re.DOTALL)
    calc_data = json.loads(m.group(1))

ipc_map = {(i['year'], i['month']): i['value'] for i in calc_data['ipc']}
latest_ipc = ipc_map[max(ipc_map.keys())]

df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')

def get_ibl(div_mode='30.0'):
    # Modes: '30.0', '30.4375', 'weeks_4.33', 'none'
    monthly_map = {}
    
    for _, row in df.iterrows():
        try:
            s = pd.to_datetime(row['Desde']).to_pydatetime()
            e = pd.to_datetime(row['Hasta']).to_pydatetime()
            val = float(row['Último Salario'])
            
            days = (e - s).days + 1
            if div_mode == '30.0': months = days / 30.0
            elif div_mode == '30.4375': months = days / 30.4375
            elif div_mode == 'none': months = 1.0 # Monthly
            else: months = (days / 7) / 4.333
            
            if months < 0.1: months = 0.1
            rate = val / months
            
            curr = datetime.datetime(s.year, s.month, 1)
            while curr <= e:
                k = curr.strftime("%Y-%m")
                monthly_map[k] = monthly_map.get(k, 0) + rate
                curr = (curr.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        except: continue
        
    all_keys = sorted(monthly_map.keys(), reverse=True)
    ibl_months = [k for k in all_keys if k < "2025-01"][:120]
    
    total_indexed = 0
    for k in ibl_months:
        y, m = map(int, k.split('-'))
        nominal = monthly_map[k]
        ipc_m = ipc_map.get((y, m), latest_ipc)
        total_indexed += nominal * (latest_ipc / ipc_m)
        
    avg_120 = total_indexed / 120
    avg_count = total_indexed / len(ibl_months) if ibl_months else 0
    return avg_120, avg_count, len(ibl_months)

res = get_ibl('30.4375')
print(f"Mode 30.4375 (Div 120): ${res[0]:,.0f}")
print(f"Mode 30.4375 (Div {res[2]}): ${res[1]:,.0f}")

# Try another logic: Max for each month
def get_ibl_max():
    monthly_map = {}
    for _, row in df.iterrows():
        try:
            s = pd.to_datetime(row['Desde']).to_pydatetime()
            e = pd.to_datetime(row['Hasta']).to_pydatetime()
            val = float(row['Último Salario'])
            curr = datetime.datetime(s.year, s.month, 1)
            while curr <= e:
                k = curr.strftime("%Y-%m")
                if k not in monthly_map: monthly_map[k] = []
                monthly_map[k].append(val)
                curr = (curr.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        except: continue
    
    total_indexed = 0
    keys = sorted(monthly_map.keys(), reverse=True)[:120]
    for k in keys:
        y, m = map(int, k.split('-'))
        nominal = max(monthly_map[k])
        ipc_m = ipc_map.get((y, m), latest_ipc)
        total_indexed += nominal * (latest_ipc / ipc_m)
    return total_indexed / 120

print(f"Mode MAX: ${get_ibl_max():,.0f}")
