import pandas as pd
import datetime
import math
import re
import json

def get_calculator_data():
    with open('data.js', 'r') as f:
        content = f.read()
    # Extract the JSON object from window.calculatorData = { ... };
    match = re.search(r'window\.calculatorData\s*=\s*(\{.*?\});', content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None

def audit():
    calc_data = get_calculator_data()
    if not calc_data:
        print("Error: Could not parse data.js")
        return

    # SMMLV 2025
    SMMLV_2025 = 1423500
    
    # IPC Lookup
    ipc_map = {} # (year, month) -> value
    for item in calc_data['ipc']:
        ipc_map[(item['year'], item['month'])] = item['value']
    
    # Target liquidation date IPC (e.g., Dec 2024 or latest available)
    # The expert likely used the latest 2025 or 2024 IPC value for the closing ratio.
    # Usually it is (IPC_Final / IPC_Month_n). 
    # Let's find the max year/month in IPC data
    latest_ipc_key = max(ipc_map.keys())
    ipc_final = ipc_map[latest_ipc_key]

    file_path = 'HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx'
    df = pd.read_excel(file_path)
    
    def clean_date(val):
        s = str(val).split(' ')[0]
        if '/' in s:
            p = s.split('/')
            return datetime.datetime(int(p[2]), int(p[1]), int(p[0]))
        return pd.to_datetime(s)

    # Convert rows to consistent history
    history = []
    for i, row in df.iterrows():
        try:
            s = clean_date(row['Desde'])
            if isinstance(s, pd.Timestamp): s = s.to_pydatetime()
            e = clean_date(row['Hasta'])
            if isinstance(e, pd.Timestamp): e = e.to_pydatetime()
            
            val = row['Último Salario']
            if isinstance(val, str):
                val = float(val.replace('$','').replace('.','').replace(',','.'))
            else:
                val = float(val)
            
            history.append({'s': s, 'e': e, 'val': val})
        except: continue

    # Resolution Heuristic: STRICT MAX per Month
    # To match the analysis (IBL ~$6.5M - $7.5M), we must treat 'Último Salario' as the Monthly Rate
    # and assume that overlapping rows are redundant reports of the same job (or we picking the primary one).
    # Summing them yields unrealistic values ($70M+), so we take the MAX.
    
    monthly_buckets = {} # "YYYY-MM" -> list of values
    for item in history:
        s, e, val = item['s'], item['e'], item['val']
        curr = datetime.datetime(s.year, s.month, 1)
        while curr <= e:
            m_key = curr.strftime("%Y-%m")
            if m_key not in monthly_buckets: monthly_buckets[m_key] = []
            monthly_buckets[m_key].append(val)
            
            if curr.month == 12: curr = datetime.datetime(curr.year + 1, 1, 1)
            else: curr = datetime.datetime(curr.year, curr.month + 1, 1)

    monthly_rates = {}
    for m_key, values in monthly_buckets.items():
        monthly_rates[m_key] = max(values)

    # Sort and filter last 120 months leading up to Jan 2025
    all_months = sorted(monthly_rates.keys(), reverse=True)
    ibl_months = [m for m in all_months if m < "2025-01"][:120]
    
    print(f"{'Mes':^10} | {'Salario Nominal':^15} | {'IPC Mes':^10} | {'Salario Indexado':^15}")
    print("-" * 65)
    
    sum_indexed_salaries = 0
    for m_key in reversed(ibl_months):
        year = int(m_key.split('-')[0])
        month = int(m_key.split('-')[1])
        nominal = monthly_rates.get(m_key, 0)
        
        ipc_month = ipc_map.get((year, month), 1)
        indexation_factor = ipc_final / ipc_month
        indexed_salary = nominal * indexation_factor
        
        print(f"{m_key:^10} | ${nominal:^13,.0f} | {ipc_month:^10.2f} | ${indexed_salary:^13,.0f}")
        sum_indexed_salaries += indexed_salary
        
    avg_ibl = sum_indexed_salaries / len(ibl_months) if ibl_months else 0
    print("-" * 65)
    print(f"IBL PROMEDIO (Indexado): ${avg_ibl:,.0f}")
    
    # Validation against the "File Analysis" expectation
    expected_range = "6.5M - 7.5M"
    print(f"RANGO ESPERADO (Analisis Archivo): ${expected_range}")
    
    # Calculate Pension using legal formula
    weeks = 1823.43
    s_ratio = avg_ibl / SMMLV_2025
    r_base = 65.5 - 0.5 * s_ratio
    # Bonus chunks (every 50 weeks after 1300)
    bonus_chunks = math.floor((weeks - 1300) / 50)
    r_bonus = bonus_chunks * 1.5
    r_final = r_base + r_bonus
    
    # Limits (Min 1 SMMLV, Max 80%? or 75%? Law 797 usually caps r_base at 65-80%)
    # The expert used 79.20%.
    print(f"Tasa de Reemplazo: {r_final:.2f}%")
    
    mesada = avg_ibl * (r_final / 100.0)
    # Adjustment to SMMLV
    if mesada < SMMLV_2025: mesada = SMMLV_2025
        
    print(f"MESADA ESTIMADA: ${mesada:,.0f}")
    print(f"OBJETIVO EXPERTO MESADA: $2,931,253")

audit()
