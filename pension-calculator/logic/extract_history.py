import pandas as pd
import json
import datetime

def parse_date(x):
    if pd.isnull(x): return None
    if isinstance(x, datetime.datetime):
        return x.strftime('%Y-%m-%d')
    # Try parsing DD/MM/YYYY
    try:
        parts = str(x).split('/')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except:
        pass
    return str(x)

try:
    df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')
    # Columns expected: Desde, Hasta, Último Salario
    # Map to start, end, salary
    history = []
    for index, row in df.iterrows():
        try:
            s_date = parse_date(row['Desde'])
            e_date = parse_date(row['Hasta'])
            salary = float(str(row['Último Salario']).replace('$','').replace('.','').replace(',','.'))
            if s_date and e_date and salary:
                history.append({
                    "start": s_date,
                    "end": e_date,
                    "salary": salary
                })
        except Exception as e:
            continue
            
    print(json.dumps(history))
except Exception as e:
    print(f"Error: {e}")
