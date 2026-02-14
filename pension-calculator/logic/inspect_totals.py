import pdfplumber
import re

files = ["Semanas Piedad.pdf", "Semanas Fran.pdf", "historiaLaboral_unlocked tia Yaneth.pdf"]

for f in files:
    print(f"\n--- Scanning {f} ---")
    with pdfplumber.open(f) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
        
        matches = re.finditer(r'\[26\]\s*TOTAL SEMANAS.*?([\d\.,]+)', all_text, re.MULTILINE | re.IGNORECASE)
        for m in matches:
            print(f"ALL MATCHES: {m.group(0)}")

    print("-" * 20)
