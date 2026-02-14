import pdfplumber
import pandas as pd

pdf_path = "historiaLaboral_unlocked tia Yaneth.pdf"
summary_data = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 2: continue
            raw_headers = " ".join([str(c or "") for c in table[0]])
            if "Aportante" in raw_headers and "Semanas" in raw_headers:
                for row in table[1:]:
                    if row and len(row) >= 9:
                        # Clean each cell to avoid multi-line text breaking the sum
                        clean_row = [str(c or "").split('\n')[0].strip() for c in row]
                        summary_data.append(clean_row)

def clean_val(v):
    if not v: return 0.0
    s = str(v).replace('.', '').replace(',', '.')
    try:
        return float(s)
    except: return 0.0

sum_sem = sum(clean_val(r[5]) for r in summary_data if len(r) > 5)
sum_total = sum(clean_val(r[8]) for r in summary_data if len(r) > 8)

print(f"Count of Rows: {len(summary_data)}")
print(f"Sum of Col 6 (Semanas): {sum_sem:.2f}")
print(f"Sum of Col 9 (Total): {sum_total:.2f}")
print(f"Target [10]: 1420.00")
print(f"Distance to 1420 (Semanas): {1420 - sum_sem:.2f}")
print(f"Distance to 1420 (Total): {1420 - sum_total:.2f}")
