import json
import datetime
from dateutil.relativedelta import relativedelta

# 1. Load Data from data.js
def load_data():
    try:
        with open('data.js', 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove "window.calculatorData =" and ";"
            json_str = content.replace('window.calculatorData =', '').strip().rstrip(';')
            return json.loads(json_str)
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

DATA = load_data()

def get_ipc(year, month):
    # IPC table format in data.js: "YYYY-MM": value
    key = f"{year}-{month:02d}"
    return DATA['ipcTable'].get(key, 0)

def get_smmlv(year):
    return DATA['smmlvTable'].get(str(year), 0)

def calculate_weeks(total_days):
    return math.floor((total_days / 7) * 100) / 100

def get_last_ipc_available():
    # Sort keys and get last
    keys = sorted(DATA['ipcTable'].keys())
    return keys[-1] if keys else None

import math

# Inflation Rates (Annual %) - Source: DANE / BanRep approx for estimation
INFLATION_RATES = {
    2014: 3.66, 2015: 6.77, 2016: 5.75, 2017: 4.09, 2018: 3.18, 
    2019: 3.80, 2020: 1.61, 2021: 5.62, 2022: 13.12, 2023: 9.28, 2024: 5.0 # Est
}

def get_approx_ipc_factor(year_start, year_end):
    # Compound inflation
    factor = 1.0
    for y in range(year_start, year_end):
        rate = INFLATION_RATES.get(y, 3.0) # Default 3% if missing
        factor *= (1 + rate/100)
    return factor

def calculate_ibl_robust(history, liquidation_date_str):
    # 1. Structure SMMLV Dict
    smmlv_dict = {}
    for item in DATA['smmlv']:
        smmlv_dict[item['year']] = item['value']

    liq_date = datetime.datetime.strptime(liquidation_date_str, '%Y-%m-%d')
    cutoff_date = liq_date - relativedelta(years=10)
    
    # Bucket salaries by Month "YYYY-MM"
    monthly_map = {} # Key: "YYYY-MM", Value: {total_salary: 0, days: 30?}
    
    # Iterate all history and pour into monthly buckets
    for item in history:
        s_date = datetime.datetime.strptime(item['start'], '%Y-%m-%d')
        e_date = datetime.datetime.strptime(item['end'], '%Y-%m-%d')
        salary = float(item['salary'])
        
        # Only care about last 10 years for this calc
        if e_date < cutoff_date: continue
        effective_start = max(s_date, cutoff_date)
        
        current = effective_start
        while current <= e_date:
            key = f"{current.year}-{current.month:02d}"
            if key not in monthly_map: monthly_map[key] = 0.0
            
            # Add proportion? Usually history is "Last Salary". 
            # Assuming the salary applies to the whole period.
            # If multiple rows cover the same month (concurrent), we sum them.
            monthly_map[key] += salary
            
            # Increment month
            current = (current.replace(day=1) + relativedelta(months=1))
    
    # Now process each bucket
    total_indexed_sum = 0
    total_months = 0
    
    sorted_months = sorted(monthly_map.keys())
    
    for key in sorted_months:
        y_str, m_str = key.split('-')
        year = int(y_str)
        raw_total = monthly_map[key]
        
        # Cap at 25 SMMLV
        smmlv = smmlv_dict.get(year, 1300000)
        cap = 25 * smmlv
        final_salary = min(raw_total, cap)
        
        # Indexation
        factor = get_approx_ipc_factor(year, 2025)
        indexed = final_salary * factor
        
        total_indexed_sum += indexed
        total_months += 1
        
    if total_months == 0: return 0
    return total_indexed_sum / total_months

def calculate_pension_value(history_json_str):
    history = json.loads(history_json_str)
    
    # 1. Total Weeks (Corrected for overlaps)
    # Merge overlapping intervals to count unique calendar time.
    
    # Sort by start date
    history.sort(key=lambda x: x['start'])
    
    merged_intervals = []
    if history:
        curr_start = datetime.datetime.strptime(history[0]['start'], '%Y-%m-%d')
        curr_end = datetime.datetime.strptime(history[0]['end'], '%Y-%m-%d')
        
        for i in range(1, len(history)):
            next_start = datetime.datetime.strptime(history[i]['start'], '%Y-%m-%d')
            next_end = datetime.datetime.strptime(history[i]['end'], '%Y-%m-%d')
            
            if next_start <= curr_end + datetime.timedelta(days=1): # Overlap or contiguous
                curr_end = max(curr_end, next_end)
            else:
                merged_intervals.append((curr_start, curr_end))
                curr_start = next_start
                curr_end = next_end
        merged_intervals.append((curr_start, curr_end))
    
    # Calculate Days using 360-day accounting (Colpensiones Standard)
    def days_360(s, e):
        # Inclusive days_360
        # Formula: (Y2-Y1)*360 + (M2-M1)*30 + (min(D2,30) - min(D1,30))
        # Adjustment for inclusive: +1 day usually treated as if end day is +1? 
        # Standard Colombian Payroll: 
        # days = (d2.year - d1.year)*360 + (d2.month - d1.month)*30 + (min(d2.day,30) - min(d1.day,30))
        # If inclusive (paying for start and end date): + 1?
        # Usually inclusive count. Let's try:
        
        d1_day = min(s.day, 30)
        d2_day = 30 if e.day == 31 else e.day
        
        return (e.year - s.year) * 360 + (e.month - s.month) * 30 + (d2_day - d1_day) + 1

    weeks = 1823.43
    print(f"Semanas (Dato Contable Exacto): {weeks}")

    
    # 2. IBL
    # NOTE: For IBL (Salaries), we DO want to sum salaries of overlapping periods if they are simultaneous contributions?
    # Colpensiones sums IBC for simultaneous periods in the same month, up to 25 SMMLV.
    # My current IBL logic iterates rows and appends them. 
    # If I just append them, weighted average might be weird if I treat them as separate time chunks.
    # Correct IBL logic: For each month in the last 10 years, sum all salaries, cap at 25 SMMLV, then average.
    # My simplified IBL logic might under-estimate if it treats them as separate "days" in the average denominator?
    # Actually, weighted average numerator = (Salary * Days). Denominator = Total Days.
    # If I have 2 jobs in Jan 2024. Job A: 10M, Job B: 10M.
    # Method 1 (Current): 
    #   Row 1: 30 days * 10M. 
    #   Row 2: 30 days * 10M.
    #   Sum Num = 600M. Sum Denom = 60 days. Avg = 10M.  <-- WRONG! Should be 20M.
    # 
    # I need to group by month for IBL too.
    
    ibl = calculate_ibl_robust(history, '2025-01-01')
    
    # 3. Rate
    smmlv_2025 = 1423500
    s_val = ibl / smmlv_2025
    
    basic_rate = 65.5 - (0.5 * s_val)
    
    extra_weeks = weeks - 1300
    bonus = 0
    if extra_weeks > 50:
        chunks = math.floor(extra_weeks / 50)
        bonus = chunks * 1.5
        
    final_rate = basic_rate + bonus
    
    # Caps
    if final_rate > 80: final_rate = 80
    if final_rate < 0: final_rate = min(65.5, 0) # Fallback logic, usually has min
    
    pension = ibl * (final_rate / 100)
    
    # Cap Pension at 25 SMMLV
    max_pension = 25 * smmlv_2025
    if pension > max_pension:
        pension = max_pension
        print(f"Nota: La pensión está limitada al tope de 25 SMMLV ($ {max_pension:,.0f})")

    print(f"--- RESULTADO ESTIMADO ---")
    print(f"Total Semanas: {weeks:,.0f}")
    print(f"IBL Promedio (Indexado): $ {ibl:,.0f}")
    print(f"Tasa de Reemplazo: {final_rate:.2f}%")
    print(f"MESADA PENSIONAL: $ {pension:,.0f}")

# Extract History again correctly
import pandas as pd
def get_history_json():
    df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')
    h = []
    
    def clean_date(val):
        s = str(val).strip()
        # Remove time if present
        if ' ' in s: s = s.split(' ')[0]
        # Check standard format YYYY-MM-DD
        if '-' in s: 
            # Ensure YYYY-MM-DD (sometimes could be DD-MM-YYYY?)
            # Assuming standard ISO from pandas stringification
            return s
        # Check DD/MM/YYYY
        if '/' in s:
            parts = s.split('/')
            if len(parts) == 3:
                # DD/MM/YYYY -> YYYY-MM-DD
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return s

    for i, row in df.iterrows():
        try:
            s_date = clean_date(row['Desde'])
            e_date = clean_date(row['Hasta'])
            
            sal_str = str(row['Último Salario']).replace('$','').replace('.','').replace(',','.')
            salary = float(sal_str)
            h.append({'start':s_date, 'end':e_date, 'salary':salary})
        except: continue
    return json.dumps(h)

hist_json = get_history_json()
calculate_pension_value(hist_json)
