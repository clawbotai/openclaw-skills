import pandas as pd
import sys

try:
    file_path = 'HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx'
    # Read first few rows
    df = pd.read_excel(file_path, nrows=5)
    print("Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].tolist())
except Exception as e:
    print("Error:", e)
