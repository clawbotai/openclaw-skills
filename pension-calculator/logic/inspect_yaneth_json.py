import requests
import os
import json

url = "http://127.0.0.1:8080/upload_pdf"
fn = "historiaLaboral_unlocked tia Yaneth.pdf"
path = os.path.join(os.getcwd(), fn)

print(f"Uploading {fn}...")
with open(path, 'rb') as f:
    response = requests.post(url, files={'file': f})

if response.status_code == 200:
    data = response.json().get('data', [])
    print(f"Total Rows: {len(data)}")
    
    # Check for invalid dates or weird patterns
    invalid_rows = 0
    total_calc = 0
    adj_row = None
    problematic = []
    
    for i, r in enumerate(data):
        d = str(r.get('Desde', ''))
        h = str(r.get('Hasta', ''))
        t = float(r.get('Total', 0))
        total_calc += t
        
        if d == '1900-01-01':
            adj_row = r
            
        if t > 0 and (d == 'None' or not d or d == 'nan'):
            problematic.append(r)
            
    print(f"Sum of TOTAL column: {total_calc:.2f}")
    print(f"Adjustment Row: {adj_row}")
    print(f"Problematic Rows (Total > 0 but No Date): {len(problematic)}")
    for p in problematic:
        print(f"  -> {p}")
    
    # Look for sum of 1314.57?
    # Maybe some rows are missing? 
    # 1420 - 1314.57 = 105.43
    for r in data:
        if abs(float(r.get('Total', 0)) - 105.43) < 0.1:
            print(f"FOUND ROW WITH 105.43 WEEKS: {r}")
else:
    print(f"Error: {response.text}")
