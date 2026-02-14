from extract_semanas import extract_labor_history
import os

# Definition of Tasks
tasks = [
    {
        "source": "Semanas Piedad.pdf",
        "output": "document for upload pension piedad.xlsx",
        "name": "PIEDAD"
    },
    {
        "source": "Semanas Fran copy.pdf",
        "output": "Pension document Fran.xlsx",
        "name": "FRAN"
    }
]

print("Starting Unified Processing...")
print("-" * 50)

for t in tasks:
    print(f"Processing {t['name']}...")
    print(f"  Input: {t['source']}")
    print(f"  Output: {t['output']}")
    
    if not os.path.exists(t['source']):
        print(f"  ERROR: Source file {t['source']} not found!")
        continue
        
    try:
        extract_labor_history(t['source'], t['output'])
        if os.path.exists(t['output']):
            print(f"  SUCCESS: {t['output']} created.")
        else:
            print(f"  FAILURE: Output file not created.")
    except Exception as e:
        print(f"  ERROR: {e}")
    print("-" * 50)
