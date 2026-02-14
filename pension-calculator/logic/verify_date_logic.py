import pandas as pd
from datetime import datetime, timedelta

# File path from extract_semanas.py
file_path = "/Users/manuelv/FreeLancing/Semanas_Cotizadas.xlsx"

try:
    df = pd.read_excel(file_path)
    print(f"Loaded {len(df)} rows from {file_path}")

    # Standardize Dates
    def parse_date(d):
        if pd.isna(d): return None
        s = str(d).strip()
        # Handle formats
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(s, fmt)
                # Force strictly to noon to avoid timezone shift issues
                return dt.replace(hour=12, minute=0, second=0)
            except:
                pass
        return None

    intervals = []
    
    for i, row in df.iterrows():
        start = parse_date(row.get('Desde'))
        end = parse_date(row.get('Hasta'))
        if start and end:
            intervals.append((start, end))

    # Sort
    intervals.sort(key=lambda x: x[0])

    # Merge Overlaps
    merged = []
    if intervals:
        curr_start, curr_end = intervals[0]
        for next_start, next_end in intervals[1:]:
            # Check overlap. Piedad Case: Many jobs start/end same dates.
            # Overlap if next_start <= curr_end + 1 day
            if next_start <= curr_end + timedelta(days=1):
                curr_end = max(curr_end, next_end)
            else:
                merged.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged.append((curr_start, curr_end))

    # Sum Days (360 Day Accounting)
    total_days_360 = 0
    for s, e in merged:
        # 360 Logic: (Y2-Y1)*360 + (M2-M1)*30 + (D2-D1) + 1
        d1 = min(s.day, 30)
        d2 = 30 if e.day == 31 else e.day
        
        days = (e.year - s.year) * 360 + (e.month - s.month) * 30 + (d2 - d1) + 1
        total_days_360 += days
    
    weeks = total_days_360 / 7
    print(f"--- RESULTS ---")
    print(f"Algorithm: Date Merge (Set Union)")
    print(f"Total Weeks: {weeks:.4f}")
    
    # Compare with Sum Total
    sum_total = pd.to_numeric(df['Total'], errors='coerce').sum()
    print(f"Sum(Total Column): {sum_total:.4f}")
    
    print(f"\nDifference (DateLogic - Target 1823.43): {weeks - 1823.43:.4f}")

except Exception as e:
    print(f"Error: {e}")
