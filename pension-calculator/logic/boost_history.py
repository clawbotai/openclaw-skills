import pandas as pd
import datetime

# Configuration
INPUT_FILE = "document for upload pension piedad.xlsx"
OUTPUT_FILE = "piedad_boosted.xlsx"
BOOST_AMOUNT = 5_000_000
START_DATE = datetime.datetime(2017, 1, 1) # 8 years back from end of 2024
END_DATE = datetime.datetime(2024, 12, 31)

print(f"Loading {INPUT_FILE}...")
df = pd.read_excel(INPUT_FILE)

def parse_date(val):
    if pd.isna(val): return None
    s = str(val).strip()
    if ' ' in s: s = s.split(' ')[0]
    if '/' in s: 
        p = s.split('/')
        if len(p) == 3: return datetime.datetime(int(p[2]), int(p[1]), int(p[0]))
    try: return pd.to_datetime(s)
    except: return None

# Apply Boost
count = 0
for i, row in df.iterrows():
    s = parse_date(row['Desde'])
    e = parse_date(row['Hasta'])
    
    if not s or not e: continue
    
    # Check overlap with boost window
    # Simple check: If the period touches the window
    overlap_start = max(s, START_DATE)
    overlap_end = min(e, END_DATE)
    
    if overlap_start <= overlap_end:
        # Boost the salary
        current_sal = float(row['Salario'])
        new_sal = current_sal + BOOST_AMOUNT
        df.at[i, 'Salario'] = new_sal
        count += 1

print(f"Boosted {count} rows by ${BOOST_AMOUNT:,.0f} between 2017 and 2024.")
df.to_excel(OUTPUT_FILE, index=False)
print(f"Saved to {OUTPUT_FILE}")
