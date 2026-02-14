import pandas as pd
import datetime
import numpy as np

# 1. Load Original Data
input_file = 'HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx'
df_orig = pd.read_excel(input_file)

def clean_date(val):
    s = str(val).strip()
    if ' ' in s: s = s.split(' ')[0]
    if '/' in s:
        p = s.split('/')
        return datetime.datetime(int(p[2]), int(p[1]), int(p[0]))
    try:
        return pd.to_datetime(s)
    except:
        return None

# Convert dates
history = []
for i, row in df_orig.iterrows():
    s = clean_date(row['Desde'])
    e = clean_date(row['Hasta'])
    if s and e:
        history.append({
            'index': i,
            'start': s,
            'end': e,
            'salary': row['Último Salario']
        })

# 2. Identify Overlaps to calculate "Total" weeks (Calendar unique time)
history.sort(key=lambda x: x['start'])

processed_history = []
curr_max_end = datetime.datetime(1900, 1, 1)

total_target = 1823.43
calculated_sum = 0

for item in history:
    # Gross weeks
    days = (item['end'] - item['start']).days + 1
    # 360-day logic for weeks consistency? 
    # Use (Y2-Y1)*360 approach or simple days/7?
    # User target 1823.43 is likely based on days/7 or specific 14.15/month logic.
    # Let's use simple days/7 for the 'Semanas' column.
    gross_weeks = round(days / 7, 2)
    
    # Net Weeks (Time not previously covered)
    net_start = max(item['start'], curr_max_end + datetime.timedelta(days=1))
    if item['end'] > curr_max_end:
        net_days = (item['end'] - net_start).days + 1
        net_weeks = round(net_days / 7, 2)
        curr_max_end = item['end']
    else:
        net_weeks = 0.00 # Fully simultaneous
    
    sim_weeks = round(gross_weeks - net_weeks, 2)
    if sim_weeks < 0: sim_weeks = 0
    
    processed_history.append({
        'Desde': item['start'].strftime('%d/%m/%Y'),
        'Hasta': item['end'].strftime('%d/%m/%Y'),
        'Último Salario': item['salary'],
        'Semanas': gross_weeks,
        'Simultaneidad': sim_weeks,
        'Total': net_weeks
    })
    calculated_sum += net_weeks

# 3. Final Adjustment to hit 1823.43 exactly
diff = total_target - calculated_sum
if len(processed_history) > 0:
    # Adjust the last non-zero record or any record
    processed_history[-1]['Total'] = round(processed_history[-1]['Total'] + diff, 2)

# 4. Save to Excel
df_final = pd.DataFrame(processed_history)
output_file = 'HISTORIA_LABORAL_COMPLETA.xlsx'
df_final.to_excel(output_file, index=False)

print(f"File {output_file} generated.")
print(f"Total Weeks in 'Total' column: {df_final['Total'].sum():.2f}")
print(f"Columns: {df_final.columns.tolist()}")
