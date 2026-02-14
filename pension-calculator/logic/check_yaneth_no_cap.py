import pdfplumber
import pandas as pd
from extract_semanas import clean_currency

pdf_path = "historiaLaboral_unlocked tia Yaneth.pdf"
detail_data = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 2: continue
            raw_headers = " ".join([str(c) for c in table[0]])
            if "Periodo" in raw_headers and "IBC" in raw_headers:
                for row in table[1:]:
                    if row and len(row) >= 12:
                        detail_data.append(row)

df = pd.DataFrame(detail_data)
sum_days = 0
for i, row in enumerate(detail_data):
    # Find which column is "Dias Cot."
    # It's usually near the end.
    # In my extract_semanas it's indexed 11. 
    # Let's try to be smart.
    if len(row) > 10:
        val = row[-2] # Penultimate column is usually Days Cot.
        try:
            sum_days += float(str(val).strip())
        except: pass

print(f"Total Rows: {len(detail_data)}")
print(f"Total Detailed Days (No Cap): {sum_days}")
print(f"Total Detailed Weeks (No Cap): {sum_days/7:.2f}")
