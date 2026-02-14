import pandas as pd

file_path = 'HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx'
df = pd.read_excel(file_path)
print("Column Count:", len(df.columns))
print("Column Names:", df.columns.tolist())
print("-" * 30)
print(df.head(5).to_string())
