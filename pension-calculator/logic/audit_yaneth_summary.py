import pdfplumber
import pandas as pd
import re
from extract_semanas import clean_numeric

pdf_path = "historiaLaboral_unlocked tia Yaneth.pdf"
summary_data = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 2: continue
            raw_headers = " ".join([str(c) for c in table[0]])
            if "Aportante" in raw_headers and "Semanas" in raw_headers:
                for row in table[1:]:
                    if row and len(row) >= 9:
                        summary_data.append(row)

df = pd.DataFrame(summary_data)
# Column 8 (index 8) is Total in Summary
print(f"Parsed {len(df)} summary rows.")
df.columns = [f"Col{i}" for i in range(len(df.columns))]

total_raw_sum = 0
for val in df["Col8"]:
    cleaned = clean_numeric(val)
    print(f"RAW: {val} | CLEANED: {cleaned}")
    total_raw_sum += cleaned

print(f"Final Sum using current clean_numeric: {total_raw_sum}")
