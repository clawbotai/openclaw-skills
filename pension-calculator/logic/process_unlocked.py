from extract_semanas import extract_labor_history
import os

pdf_file = "/Users/manuelv/FreeLancing/HISTORIA_LABORAL_UNIFICADA20251227_01__unlocked.pdf"
output_file = "/Users/manuelv/FreeLancing/Upload_For_App_Unlocked.xlsx"

print(f"Processing PDF: {pdf_file}")
print(f"Target Output: {output_file}")

if not os.path.exists(pdf_file):
    print("Error: Input PDF not found!")
else:
    extract_labor_history(pdf_file, output_file)
    if os.path.exists(output_file):
        print("Success! File generated.")
    else:
        print("Error: Output file was not generated.")
