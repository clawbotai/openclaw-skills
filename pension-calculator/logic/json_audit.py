import requests
import os
import json

url = "http://127.0.0.1:8080/upload_pdf"
files = ["Semanas Piedad.pdf", "Semanas Fran.pdf", "historiaLaboral_unlocked tia Yaneth.pdf"]

for fn in files:
    path = os.path.join(os.getcwd(), fn)
    print(f"\n--- Testing {fn} ---")
    with open(path, 'rb') as f:
        response = requests.post(url, files={'file': f})
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        total_sum = sum(float(r.get('Total', 0)) for r in data)
        print(f"Total Sum: {total_sum:.2f}")
        
        # Check for 1314.57 or 1700.67 or 1396.18
        # Maybe it's the sum EXCLUDING the adjustment row?
        no_adj_sum = sum(float(r.get('Total', 0)) for r in data if r.get('Desde') != '2024-12-31')
        print(f"Sum (No Adj): {no_adj_sum:.2f}")
        
        # Check for any row with these exact values
        targets = [1314.57, 1700.67, 1396.18, 105.43, 122.76, 105.11]
        for r in data:
            v = float(r.get('Total', 0))
            for t in targets:
                if abs(v - t) < 0.1:
                    print(f"FOUND TARGET VALUE {t} in row: {r}")
    else:
        print(f"Error: {response.text}")
