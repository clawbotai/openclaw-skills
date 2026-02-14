import pandas as pd

# Path to the generated Excel file from the server
file_path = "/Users/manuelv/FreeLancing/Semanas_Cotizadas.xlsx"

try:
    df = pd.read_excel(file_path)
    print("Files Loaded.")
    print(f"Columns: {df.columns.tolist()}")

    total_semanas = df['Semanas'].sum()
    total_sim = df['Sim'].sum()
    total_col = df['Total'].sum()

    calc_net = total_semanas - total_sim

    print(f"\n--- GLOBAL SUMS ---")
    print(f"Sum(Semanas): {total_semanas:.2f}")
    print(f"Sum(Sim):    {total_sim:.2f}")
    print(f"Calculated Net (Semanas - Sim): {calc_net:.2f}")
    print(f"Sum(Total Column):              {total_col:.2f}")

    print(f"\nDifference (Calc Net - Total Col): {calc_net - total_col:.4f}")

    # Find Mismatches
    print(f"\n--- ROW MISMATCHES (Semanas - Sim != Total) ---")
    df['Net_Calc'] = df['Semanas'] - df['Sim']
    df['Diff'] = df['Net_Calc'] - df['Total']
    
    # Filter rows with significant difference (ignore floating point noise)
    mismatches = df[df['Diff'].abs() > 0.01]
    
    if not mismatches.empty:
        print(f"Found {len(mismatches)} rows where the math doesn't match:")
        for idx, row in mismatches.iterrows():
            print(f"Row {idx+1}: Sem: {row['Semanas']} - Sim: {row['Sim']} = {row['Net_Calc']:.2f} | Total Col Says: {row['Total']} (Diff: {row['Diff']:.2f})")
    else:
        print("No row-level mismatches found. The Total column is mathematically consistent with Semanas - Sim.")

except Exception as e:
    print(f"Error analyzing file: {e}")
