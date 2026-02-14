import pandas as pd
import os

# Input and Output paths
input_excel = "/Users/manuelv/FreeLancing/HISTORIA_LABORAL_UNIFICADA20251227_01_.xlsx"
output_excel = "/Users/manuelv/FreeLancing/document for upload pension piedad.xlsx"

print(f"Reading source: {input_excel}")

try:
    df_source = pd.read_excel(input_excel)
    
    # Create target dataframe structure
    df_target = pd.DataFrame()
    
    # Map columns
    # Source has: 'Desde', 'Hasta', 'Último Salario'
    # Target needs: 'Desde', 'Hasta', 'Salario', 'Semanas', 'Lic', 'Sim', 'Total'
    
    df_target['Desde'] = df_source['Desde']
    df_target['Hasta'] = df_source['Hasta']
    df_target['Salario'] = df_source['Último Salario']
    
    # Fill missing columns with 0 or default
    df_target['Semanas'] = 0
    df_target['Lic'] = 0
    df_target['Sim'] = 0
    df_target['Total'] = 0 
    
    # Logic to calculate Total? The app calculates it from Sem+Lic-Sim. 
    # If the source doesn't have weeks, we leave it as 0? 
    # The previous extraction logic extracted 'Semanas' from the PDF summary table.
    # The source Excel seems to be a simplified version. 
    # Let's check if 'Semanas' is in source?
    # The quick inspection showed: Index(['Desde', 'Hasta', 'Último Salario'], dtype='object')
    # So 'Semanas' is missing. 
    # Use a basic calculation for 'Total' based on dates as a fallback?
    # Or leave as 0? 
    # App.js has fallback logic: "Fall back: Date-based logic with overlap handling" if explicit weeks are missing.
    # So leaving 0 is safe.
    
    print("Columns mapped. Saving to output...")
    
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_target.to_excel(writer, sheet_name='Calculations', index=False)
        
    print(f"Success! Generated: {output_excel}")
    print(df_target.head())

except Exception as e:
    print(f"Error processing excel: {e}")
