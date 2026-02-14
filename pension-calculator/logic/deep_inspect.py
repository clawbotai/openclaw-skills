import pandas as pd

file_path = 'HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx'
xls = pd.ExcelFile(file_path)

print("Sheet names:", xls.sheet_names)

for sheet in xls.sheet_names:
    print(f"\n--- Sheet: {sheet} ---")
    df = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=10)
    print(df.to_string())
