import json
from itertools import combinations

with open('last_json_response.json', 'r') as f:
    data = json.load(f)['data']

target = 105.43
epsilon = 0.1

print(f"Total rows: {len(data)}")

# check rows with issues
issues = []
zeros = []
weird_dates = []

for i, r in enumerate(data):
    w = float(r.get('Total', 0))
    s = r.get('Salario')
    d1 = r.get('Desde')
    d2 = r.get('Hasta')
    
    if not d1 or not d2:
        weird_dates.append((i, r))
    
    if s is None or s == '':
        issues.append((i, r))
    
    if w > 0 and (not d1 or not d2):
         print(f"Row {i} has weeks {w} but missing dates: {r}")

# Check sum of weird dates
sum_weird = sum(float(r[1].get('Total', 0)) for r in weird_dates)
print(f"Sum of rows with missing dates: {sum_weird}")

# Check sum of rows with 0 salary (maybe excluded?)
# actually app.js requires salaryVal. If salary is 0 it should be fine?
# unless parseSalary returns null for 0?

# Try to find a subset that sums to gap
weeks = [float(r.get('Total', 0)) for r in data]
total_weeks = sum(weeks)
print(f"Total Weeks: {total_weeks}")
print(f"Target Gap: {target}")

# Check date formats
bad_dates = []
for i, r in enumerate(data):
    d = r.get('Desde', '')
    if '/' in d:
        # Check standard format
        parts = d.split('/')
        if len(parts) != 3:
            bad_dates.append((i, r))
    else:
        # Maybe YYYY-MM-DD?
        pass

print(f"Bad date formats found: {len(bad_dates)}")

# Subset sum?
# Try to find if the missing amount is from specific rows
# Maybe filter those with '/' in dates?
slash_weeks = sum(float(r.get('Total', 0)) for r in data if '/' in r.get('Desde', ''))
dash_weeks = sum(float(r.get('Total', 0)) for r in data if '-' in r.get('Desde', ''))

print(f"Slash Date Weeks: {slash_weeks}")
print(f"Dash Date Weeks: {dash_weeks}")

# Find subset of detailed rows sum to 105.43
detailed_rows = [r for r in data if '/' in r.get('Desde', '')]
detailed_weeks = [float(r.get('Total', 0)) for r in detailed_rows]

print(f"Detailed Rows Count: {len(detailed_rows)}") # Should be ~298
print(f"Detailed Weeks Sum: {sum(detailed_weeks)}") # Should be 1260.43

# We need a subset of these that sums to 105.43
# Since 105.43 is small relative to 1260, maybe it's few rows?
# Or maybe it's a specific block?

# Heuristic: Check if any single row is 105.43 (checked, no)
# Check if sum of 2, 3, 4, 5 rows matches?
from itertools import combinations

found_subset = False
for r in range(1, 6):
    print(f"Checking combinations of size {r}...")
    for c in combinations(enumerate(detailed_weeks), r):
        # c is tuple of (index, value)
        s = sum(x[1] for x in c)
        if abs(s - target) < 0.01:
            print(f"FOUND SUBSET SUM! Indices: {[x[0] for x in c]}")
            print(f"Values: {[x[1] for x in c]}")
            for idx in [x[0] for x in c]:
                print(f"Row {idx}: {detailed_rows[idx]}")
            found_subset = True
            break
    if found_subset: break

if not found_subset:
    print("No small subset found. Maybe it's a large chunk?")
    # Check if a contiguous block sums to 105.43?
    for i in range(len(detailed_weeks)):
        current_sum = 0
        for j in range(i, len(detailed_weeks)):
            current_sum += detailed_weeks[j]
            if abs(current_sum - target) < 0.01:
                print(f"FOUND CONTIGUOUS BLOCK {i} to {j}")
                print(f"Rows: {detailed_rows[i:j+1]}")
                found_subset = True
                break
        if found_subset: break
