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
    factor = 1.0
    for y in range(year_salary, year_liq):
        rate = DATA['inflation'].get(y, 3.0)
        factor *= (1 + rate/100)
    return factor

def audit_calculation():
    df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')
    
    history = []
    
    def clean_date(val):
        s = str(val).split(' ')[0]
        if '/' in s:
            p = s.split('/')
            return f"{p[2]}-{p[1]}-{p[0]}"
        return s

    print(f"{'Periodo':^25} | {'Valor Reportado':^15} | {'Meses':^5} | {'Salario Mensual Calc':^15}")
    print("-" * 80)
    
    cutoff_date = datetime.datetime(2015, 1, 1)
    
    monthly_salaries = []
    
    for i, row in df.iterrows():
        try:
             s_str = clean_date(row['Desde'])
             e_str = clean_date(row['Hasta'])
             val = float(str(row['Último Salario']).replace('$','').replace('.','').replace(',','.'))
             
             s_date = datetime.datetime.strptime(s_str, '%Y-%m-%d')
             e_date = datetime.datetime.strptime(e_str, '%Y-%m-%d')
             
             if e_date < cutoff_date: continue
             
             # Calculate duration in months roughly
             days = (e_date - s_date).days + 1
             months = days / 30.0
             if months < 1: months = 1 # Avoid div/0 or huge spikes for tiny periods
             
             monthly_wage = val / months
             
             # Print sample
             if i % 5 == 0: # Print some rows
                 print(f"{s_str} - {e_str} | ${val:,.0f} | {months:.1f} | ${monthly_wage:,.0f}")
             
             # Indexation
             year = s_date.year
             factor = get_ipc_factor(year, 2025)
             indexed = monthly_wage * factor
             
             monthly_salaries.append(indexed)
             
        except: continue
        
    avg_ibl = sum(monthly_salaries) / len(monthly_salaries)
    print("\n" + "="*50)
    print(f"IBL Estimado (Promedio Mensualizado): ${avg_ibl:,.0f}")
    
    # Quick Pension Est
    # weeks 1823.43 -> Rate ~70.5%
    pension = avg_ibl * 0.705
    print(f"Mesada Estimada: ${pension:,.0f}")

audit_calculation()
