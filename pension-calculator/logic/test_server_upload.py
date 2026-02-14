import requests
import os

url = "http://127.0.0.1:8080/upload_pdf"
files_to_test = ["Semanas Piedad.pdf", "Semanas Fran.pdf", "historiaLaboral_unlocked tia Yaneth.pdf"]

for fn in files_to_test:
    path = os.path.join(os.getcwd(), fn)
    print(f"\nUploading {fn}...")
    with open(path, 'rb') as f:
        response = requests.post(url, files={'file': f})
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        print(f"Server returned {len(data)} records.")
        # Calculate Total from JSON
        total_weeks = 0
        adj_weeks = 0
        for r in data:
            val = float(r.get('Total', 0))
            total_weeks += val
            if r.get('Desde') == '2025-01-01':
                adj_weeks = val
                print(f"  -> Found Adjustment Row: {val}")
        
        print(f"  -> Total Weeks Sum: {total_weeks:.2f}")
    else:
        print(f"Error: {response.text}")
