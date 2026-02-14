import pandas as pd
import datetime

def analyze():
    df = pd.read_excel('HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx')
    
    def clean_date(val):
        s = str(val).split(' ')[0]
        if '/' in s:
            p = s.split('/')
            return datetime.datetime(int(p[2]), int(p[1]), int(p[0]))
        return pd.to_datetime(s)

    cutoff = datetime.datetime(2015, 1, 1)
    monthly_data = []

    for i, row in df.iterrows():
        try:
            s = clean_date(row['Desde'])
            e = clean_date(row['Hasta'])
            if e < cutoff: continue
            
            val = float(str(row['Último Salario']).replace('$','').replace('.','').replace(',','.'))
            days = (e - s).days + 1
            months = days / 30.0
            if months < 0.1: months = 0.1
            
            monthly = val / months
            
            # Simplified Indexing (Approx)
            factor = 1.0
            if s.year == 2018: factor = 1.6
            if s.year == 2019: factor = 1.5
            if s.year == 2024: factor = 1.05
            
            indexed = monthly * factor
            
            # Create records for each month in the range
            curr = s
            while curr <= e:
                monthly_data.append({
                    'year': curr.year,
                    'month': curr.month,
                    'indexed': indexed
                })
                # Move to next month
                if curr.month == 12:
                    curr = datetime.datetime(curr.year + 1, 1, 1)
                else:
                    curr = datetime.datetime(curr.year, curr.month + 1, 1)

        except: continue

    df_monthly = pd.DataFrame(monthly_data)
    print("Total Months Found:", len(df_monthly))
    
    print("\n--- TOP 10 MONTHS ---")
    print(df_monthly.sort_values('indexed', ascending=False).head(10).to_string())
    
    print("\n--- BOTTOM 10 MONTHS ---")
    print(df_monthly.sort_values('indexed', ascending=True).head(10).to_string())
    
    print("\nAverage of all found months:", df_monthly['indexed'].mean())

analyze()
