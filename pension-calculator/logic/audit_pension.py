import json
import datetime
import math
from dateutil.relativedelta import relativedelta
import pandas as pd

# 1. DATA
DATA = {
    'smmlv': {
        2014: 616000, 2015: 644350, 2016: 689455, 2017: 737717, 
        2018: 781242, 2019: 828116, 2020: 877803, 2021: 908526, 
        2022: 1000000, 2023: 1160000, 2024: 1300000, 2025: 1423500
    },
    'inflation': {
        2015: 6.77, 2016: 5.75, 2017: 4.09, 2018: 3.18, 
        2019: 3.80, 2020: 1.61, 2021: 5.62, 2022: 13.12, 
        2023: 9.28, 2024: 5.0 # Est
    }
}

def get_ipc_factor(year_salary, year_liq=2025):
    # Standard: Product of (1+inflation) from year_salary+1 to year_liq-1?
    # Or to year_liq? 
    # Usually: Value_2015 * (1+Inf_2015) * (1+Inf_2016) ... * (1+Inf_2024) = Value_2025
    factor = 1.0
    for y in range(year_salary, year_liq):
        rate = DATA['inflation'].get(y, 3.0)
        factor *= (1 + rate/100)
    return factor

def audit_calculation():
    # 1. Load History
    # (Simulated loading from the file again would be best, but let's use the known pattern for the "Last 10 Years" which is the contentious part)
    # Based on the user's file content extracted previously:
    # 2015: ~8.9M. 2016: ~9.6M. 2017: ~25M... 2024: ~120M
    
    # Let's re-extract to be precise
    df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')
    
    # Prepare list
    history = []
    
    def clean_date(val):
        s = str(val).split(' ')[0]
        if '/' in s:
            p = s.split('/')
            return f"{p[2]}-{p[1]}-{p[0]}" # DD/MM/YYYY -> ISO
        return s

    for i, row in df.iterrows():
        try:
             s = clean_date(row['Desde'])
             e = clean_date(row['Hasta'])
             sal = float(str(row['Último Salario']).replace('$','').replace('.','').replace(',','.'))
             history.append({'start': s, 'end': e, 'salary': sal})
        except: continue
        
    cutoff_date = datetime.datetime(2015, 1, 1) # Approx last 10 years from 2025
    
    print(f"{'AÑO':^6} | {'SALARIO REAL':^15} | {'TOPE (25 SM)':^15} | {'SALARIO BASE':^15} | {'FACTOR IPC':^10} | {'SALARIO INDEXADO (2025)':^22}")
    print("-" * 100)
    
    yearly_sums = {} # To aggregate by year for clearer display
    
    total_indexed_val = 0
    total_days = 0
    
    for item in history:
        s_date = datetime.datetime.strptime(item['start'], '%Y-%m-%d')
        e_date = datetime.datetime.strptime(item['end'], '%Y-%m-%d')
        
        if e_date < cutoff_date: continue
        
        eff_start = max(s_date, cutoff_date)
        days = (e_date - eff_start).days + 1
        year = eff_start.year
        
        raw_sal = item['salary']
        
        # Apply Cap
        smmlv = DATA['smmlv'].get(year, 0)
        cap = 25 * smmlv
        used_sal = min(raw_sal, cap)
        
        # Factor
        factor = get_ipc_factor(year, 2025)
        indexed = used_sal * factor
        
        # Weighted accumulation
        total_indexed_val += (indexed * days)
        total_days += days
        
        # Log for table (Aggregate by year roughly)
        if year not in yearly_sums: yearly_sums[year] = {'raw': [], 'used': [], 'indexed': [], 'days': 0}
        yearly_sums[year]['raw'].append(raw_sal)
        yearly_sums[year]['used'].append(used_sal)
        yearly_sums[year]['indexed'].append(indexed)
        yearly_sums[year]['days'] += days

    # Print Markdown Table for User
    print("\n### Detalle del Cálculo IBL (Últimos 10 Años)")
    print("| Año | Días | Salario Reportado | IPC Factor | Salario Indexado (2025) |")
    print("| :--- | :---: | :---: | :---: | :---: |")
    
    for y in sorted(yearly_sums.keys()):
        d = yearly_sums[y]
        avg_raw = sum(d['raw'])/len(d['raw'])
        avg_ind = sum(d['indexed'])/len(d['indexed'])
        days = d['days']
        factor = get_ipc_factor(y, 2025)
        
        print(f"| {y} | {days} | $ {avg_raw:,.0f} | {factor:.4f} | $ {avg_ind:,.0f} |")
        
    final_ibl = total_indexed_val / total_days
    print(f"\n**IBL Final Promedio**: $ {final_ibl:,.0f}")
    
    # Rate Verification
    smmlv_2025 = DATA['smmlv'][2025]
    s_val = final_ibl / smmlv_2025
    print(f"\nCálculo de Tasa:")
    print(f"IBL / SMMLV 2025 = ${final_ibl:,.0f} / ${smmlv_2025:,.0f} = {s_val:.2f} salarios mínimos")
    
    basic_rate = 65.5 - (0.5 * s_val)
    print(f"Tasa Base (r = 65.5 - 0.5*s) = {65.5} - {0.5*s_val:.2f} = {basic_rate:.2f}%")
    
    weeks = 1823.43
    extra_weeks = weeks - 1300
    bonus_blocks = math.floor(extra_weeks / 50)
    bonus = bonus_blocks * 1.5
    print(f"Semanas Extra: {weeks} - 1300 = {extra_weeks:.2f}")
    print(f"Bloques de 50 semanas: {bonus_blocks}")
    print(f"Bono de Semanas: {bonus_blocks} * 1.5% = {bonus}%")
    
    final_rate = basic_rate + bonus
    print(f"Tasa Final: {basic_rate:.2f}% + {bonus}% = {final_rate:.2f}%")
    
    pension = final_ibl * (final_rate/100)
    print(f"\nMESADA PENSIONAL: ${pension:,.2f}")

audit_calculation()
