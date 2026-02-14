from extract_semanas import extract_labor_history
import json

pdf_file = "/Users/manuelv/FreeLancing/HISTORIA_LABORAL_UNIFICADA20251227_01_.pdf"
data = extract_labor_history(pdf_file, None)

print("Total Records:", len(data))
if len(data) > 0:
    print("Sample Record 1:", data[0])
    for i in range(min(5, len(data))):
        print(f"Row {i}: Salario = {data[i].get('Salario')} (Type: {type(data[i].get('Salario'))})")
