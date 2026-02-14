import pdfplumber
import pandas as pd
import re
import os

def clean_currency(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    if not s: 
        return 0.0

    cleaned = s.replace('$', '').replace(' ', '')
    
    # Heuristic for 1.234.567,89 (Colombia) vs 1111.11 (Float String)
    dots = cleaned.count('.')
    commas = cleaned.count(',')
    
    if dots > 1:
        # Multiple dots = Thousands (2.112.000)
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif dots == 1:
        # One dot. Ambiguous: 1.234 (Thousands?) or 1234.5 (Decimal?)
        if commas > 0:
            # 1.234,56 -> Remove dot, comma to dot
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # No commas. 1.234 vs 1234.5
            parts = cleaned.split('.')
            if len(parts[1]) == 3:
                # 1.234 -> Likely thousands, unless strict PDF float
                # But PDFplumber usually gives EXACT text.
                # In Colombia PDF, 1.234 is thousands.
                cleaned = cleaned.replace('.', '')
            else:
                 # 1234.5 or 1234.56 -> Likely decimal.
                 pass
    else:
        # No dots.
        if commas > 0:
            # 1234,56 -> Replace comma with dot
            cleaned = cleaned.replace(',', '.')
            
    try:
        val = float(cleaned)
        return val
    except ValueError:
        return 0.0

def clean_numeric(value):
    if not value or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip().replace('$', '').replace(' ', '')
    if not s: return 0.0

    # Heuristic similar to clean_currency but simpler
    dots = s.count('.')
    commas = s.count(',')

    if dots == 1 and commas == 0:
        parts = s.split('.')
        if len(parts[1]) == 3 and float(parts[0]) > 0:
            # 1.420 -> Thousands
            s = s.replace('.', '')
        else:
            # 70.71 or 4.29 -> Keep dot
            pass
    elif dots > 0 and commas > 0:
        # 1.420,00 -> Remove dot, comma to dot
        s = s.replace('.', '').replace(',', '.')
    elif commas > 0:
        # 1420,00 -> Comma to dot
        s = s.replace(',', '.')
    
    try:
        return float(s)
    except ValueError:
        return 0.0

def extract_labor_history(pdf_path, output_excel):
    summary_data = []
    detail_data = []

    # Scan for "Gran Total" text pattern
    grand_total_weeks = 0
    
    print(f"Opening PDF: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}...")
            
            # Text Scan for Gran Total
            text = page.extract_text()
            if text:
                # Pattern: [26]TOTAL SEMANAS ... 1.501,29 OR 1501,29
                # Regex to capture the value at the end of the line
                # Look for "[26]" and "TOTAL SEMANAS" and capture the number at the end
                # Ultra-robust regex for Item 26
                # Look for "[26]" and "TOTAL SEMANAS" and then capture the last number on that block
                # We use a pattern that matches [26] TOTAL SEMANAS and finds the first following number that isn't a bracketed index
                match = re.search(r'\[26\]\s*TOTAL SEMANAS.*?(?:[\):])\s*([\d\.,]+)', text, re.DOTALL | re.IGNORECASE)
                if not match:
                    # Very loose fallback: just look for [26] and capture the first number after some distance
                    match = re.search(r'\[26\].*?TOTAL SEMANAS.*?(\d+[\d\.,]*)', text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    val_str = match.group(1)
                    # Exclude small numbers that might be indices if they are exactly [10], [21], etc.
                    # A total is typically >= 10.0
                    gt = clean_numeric(val_str)
                    if gt > grand_total_weeks:
                        print(f"  -> Found Gran Total Candidate (Robust Match): {val_str} -> {gt}")
                        grand_total_weeks = gt
                        
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # Check for headers to identify table type
                # Clean headers and join multi-line headers if necessary
                raw_headers = [str(cell).strip() if cell else "" for cell in table[0]]
                headers_str = " ".join(raw_headers)
                print(f"  Headers found: {headers_str[:100]}...")
                
                # Table 1: Summary by Employer
                # Search for key headers in the first row
                has_aportante = "Aportante" in headers_str or "Nombre o Razón Social" in headers_str
                has_dates = "Desde" in headers_str and "Hasta" in headers_str
                has_weeks = "Semanas" in headers_str
                is_summary = has_aportante and has_dates and has_weeks and len(raw_headers) < 12
                
                if is_summary:
                    print(f"  -> Matched Summary Table")
                    for row in table[1:]:
                        if row and any(row) and len(row) >= 6:
                            summary_data.append(row)
                
                # Table 2: Detailed Payments
                headers_clean = headers_str.lower().replace('í', 'i').replace('ó', 'o')
                if ("periodo" in headers_clean or "ciclo" in headers_clean) and \
                   ("ibc" in headers_clean or "salario" in headers_clean or "cotizacion" in headers_clean):
                    print(f"  -> Matched Detailed Table")
                    for row in table[1:]:
                        if row and any(row) and len(row) >= 10 and not any(h in str(cell) for cell in row for h in ["Periodo", "Período", "Ciclo"]):
                            detail_data.append(row)

    # Process Summary Table
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        cols = [
            "Identificación Aportante", "Nombre o Razón Social", "Desde", "Hasta", 
            "Último Salario", "Semanas", "Lic", "Sim", "Total"
        ]
        df_summary = df_summary.iloc[:, :len(cols)]
        df_summary.columns = cols
        
        # Clean data
        df_summary["Identificación Aportante"] = df_summary["Identificación Aportante"].astype(str).str.split('.').str[0]
        df_summary["Último Salario"] = df_summary["Último Salario"].apply(clean_currency)
        df_summary["Semanas"] = df_summary["Semanas"].apply(clean_numeric)
        df_summary["Total"] = df_summary["Total"].apply(clean_numeric)
        
        df_summary["Desde"] = df_summary["Desde"].astype(str).str.strip()
        df_summary["Hasta"] = df_summary["Hasta"].astype(str).str.strip()
        
        print(f"Extracted {len(df_summary)} summary rows.")
    else:
        df_summary = pd.DataFrame()

    # Process Detailed Table
    if detail_data:
        df_detail = pd.DataFrame(detail_data)
        cols_detail = [
            "Identificación Aportante", "Nombre o Razón Social", "RA", "Periodo", "Fecha De Pago", 
            "Referencia de Pago", "IBC Reportado", "Cotización Pagada", "Cotización Mora Sin Intereses", "Nov.", 
            "Días Rep.", "Días Cot.", "Observación"
        ]
        if df_detail.shape[1] > len(cols_detail):
            df_detail = df_detail.iloc[:, :len(cols_detail)]
        elif df_detail.shape[1] < len(cols_detail):
            cols_detail = cols_detail[:df_detail.shape[1]]
        df_detail.columns = cols_detail
        
        # Formatting
        df_detail["Identificación Aportante"] = df_detail["Identificación Aportante"].astype(str).str.split('.').str[0]
        
        # Convert Periodo (YYYYMM) to DD/MM/YYYY (01/MM/YYYY)
        def format_period(p):
            p_str = str(p).split('.')[0].strip()
            if len(p_str) == 6:
                return f"01/{p_str[4:6]}/{p_str[0:4]}"
            return p_str
        
        df_detail["Periodo"] = df_detail["Periodo"].apply(format_period)
        df_detail["Fecha De Pago"] = df_detail["Fecha De Pago"].astype(str).str.strip()
        
        col_ibc = "IBC Reportado"
        if "IBC Reported" in df_detail.columns: col_ibc = "IBC Reported"
        df_detail[col_ibc] = df_detail[col_ibc].apply(clean_currency)
        
        df_detail["Días Cot."] = pd.to_numeric(df_detail["Días Cot."], errors='coerce').fillna(0).astype(int)
        print(f"Extracted {len(df_detail)} detailed rows.")
    else:
        df_detail = pd.DataFrame()

    # Create simplified dataframe for App Upload
    # ROBUST METHOD: Group by Period from Detailed Table
    df_app = pd.DataFrame()

    if not df_detail.empty:
        print("Using Detailed Table with Monthly Grouping...")
        
        def get_ym(p):
            try:
                parts = p.split('/')
                if len(parts) == 3: return f"{parts[2]}-{parts[1]}"
                return p
            except:
                return p

        df_detail['YM'] = df_detail['Periodo'].apply(get_ym)
        
        col_ibc = "IBC Reportado"
        if "IBC Reported" in df_detail.columns: col_ibc = "IBC Reported"
        
        # Group
        df_grouped = df_detail.groupby('YM').agg({
            col_ibc: 'sum', # Sum Total Income
            'Días Cot.': 'sum',
            'Periodo': 'first'
        }).reset_index()
        
        # Cap Days at 30
        df_grouped['Dias_Final'] = df_grouped['Días Cot.'].apply(lambda x: min(x, 30))
        df_grouped = df_grouped.sort_values('YM')
        
        import calendar
        
        starts = []
        ends = []
        for idx, row in df_grouped.iterrows():
            p = row['Periodo'] # Format 01/MM/YYYY
            try:
                parts = p.split('/')
                month = int(parts[1])
                year = int(parts[2])
                
                # Start is always 01
                s = p
                
                # End must be valid calendar day
                # Colpensiones considers 30 days for accounting, but for Date Object we need valid day
                # The 'Semanas' column already contains the 30-day logic (4.29 weeks)
                # So we can safely set the DATE to the actual end of month (28, 29, 30, 31)
                last_day = calendar.monthrange(year, month)[1]
                
                # However, for 31-day months, Colpensiones might want 30?
                # Actually, the App uses the dates for IBL indexing.
                # If we put 31, it's fine.
                # If we put 28 (Feb), it's fine.
                # The key is that the DATE STRING must be valid for the browser.
                
                e = f"{last_day:02d}/{month:02d}/{year}"
            except:
                s = str(p); e = str(p)
            starts.append(s)
            ends.append(e)

        df_app = pd.DataFrame()
        df_app["Desde"] = starts
        df_app["Hasta"] = ends
        df_app["Salario"] = df_grouped[col_ibc].values
        df_app["Semanas"] = df_grouped['Dias_Final'].values / 7
        df_app["Lic"] = 0
        df_app["Sim"] = 0
        df_app["Total"] = df_app["Semanas"] # Base count

        df_app["Total"] = df_app["Semanas"] # Base count

    elif not df_summary.empty:
        print("Fallback to Summary Table (Original Method)...")
        df_app = pd.DataFrame()
        df_app["Desde"] = df_summary["Desde"]
        df_app["Hasta"] = df_summary["Hasta"]
        df_app["Salario"] = df_summary["Último Salario"]
        df_app["Semanas"] = df_summary["Semanas"]
        df_app["Lic"] = df_summary["Lic"].apply(clean_numeric) if "Lic" in df_summary else 0
        df_app["Sim"] = df_summary["Sim"].apply(clean_numeric) if "Sim" in df_summary else 0
        df_app["Total"] = df_summary["Total"]

    # CLEANUP: Remove any rows with None or Empty dates BEFORE calculating sum
    if not df_app.empty:
        df_app = df_app[df_app["Desde"].notna() & (df_app["Desde"].astype(str) != 'None') & (df_app["Desde"].astype(str) != '')]

    if not df_app.empty:
        # Round ALL weeks to 2 decimals to match Frontend Display Math
        df_app["Semanas"] = df_app["Semanas"].round(2)
        df_app["Total"] = df_app["Total"].round(2)

        # CHECK TOTAL WEEKS DISCREPANCY
        target_weeks = 0
        
        # Priority 1: Text Scan
        if grand_total_weeks > 0:
            target_weeks = grand_total_weeks
            print(f"DEBUG: Using Exact Target Weeks from Text: {target_weeks}")
            
        # Priority 2: Summary Sum (as backup)
        elif not df_summary.empty and "Total" in df_summary.columns:
             try:
                target_weeks = df_summary["Total"].apply(clean_numeric).sum()
                print(f"DEBUG: Target Weeks from Summary Sum: {target_weeks}")
             except:
                pass
        
        # Use the ROUNDED sum to match what the browser will see
        current_sum = df_app["Semanas"].sum() 
        print(f"DEBUG: [FINAL] target_weeks={target_weeks}, rounded_current_sum={current_sum}")
        
        # Tolerance: if missing more than 0.01 weeks (accounting for rounding)
        if target_weeks > (current_sum + 0.01):
            diff = target_weeks - current_sum
            print(f"Adding Adjustment Row (Historia Consolidada) for {diff:.2f} weeks to match Official Total.")
            
            adj_row = pd.DataFrame([{
                "Desde": "2024-12-31", # More modern date
                "Hasta": "2024-12-31",
                "Salario": 0,
                "Semanas": diff,
                "Lic": 0,
                "Sim": 0,
                "Total": diff
            }])
            df_app = pd.concat([df_app, adj_row], ignore_index=True)

        # Save to a new simplified Excel file (Optional, for debugging)
        if output_excel:
            try:
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_app.to_excel(writer, sheet_name='Calculations', index=False)
                print(f"Simplified Excel file saved to: {output_excel}")
            except Exception as e:
                print(f"Warning: Could not save Excel debug file: {e}")
            
        # Return data for Server
        records = df_app.where(pd.notnull(df_app), None).to_dict('records')
        return records
    
    return []
