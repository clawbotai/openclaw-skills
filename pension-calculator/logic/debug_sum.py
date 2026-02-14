import json

with open('last_json_response.json', 'r') as f:
    data = json.load(f)['data']

total = 0
for i, r in enumerate(data):
    val = float(r.get('Total') or 0)
    total += val
    # print(f"{i}: {val}")

print(f"Total Sum from JSON: {total}")

adj = [r for r in data if r.get('Desde') == '2024-12-31']
if adj:
    print(f"Adjustment Row: {adj[0]['Total']}")

print(f"Detailed Sum: {total - float(adj[0]['Total'])}")
print(f"Difference from 1421.24: {1421.24 - total}")
