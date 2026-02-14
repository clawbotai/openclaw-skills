import pandas as pd

def verify_excel(file_path):
    print(f"Verifying Excel file: {file_path}")
    try:
        xls = pd.ExcelFile(file_path)
        print(f"Sheets found: {xls.sheet_names}")
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"\nSheet: {sheet_name}")
            print(f"  Shape: {df.shape}")
            print("  First 5 rows:")
            print(df.head().to_string())
            
            # Check for NaN in critical columns
            if sheet_name == 'Summary_By_Employer' and not df.empty:
                print(f"  Total Semanas Sum: {df['Total'].sum()}")
                print(f"  Date Sample (Desde): {df['Desde'].iloc[0]}")
            if sheet_name == 'Detailed_Payments' and not df.empty:
                print(f"  Total Días Cot. Sum: {df['Días Cot.'].sum()}")
                print(f"  Date Sample (Periodo): {df['Periodo'].iloc[0]}")
                
    except Exception as e:
        print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    verify_excel("/Users/manuelv/FreeLancing/Semanas_Cotizadas.xlsx")
