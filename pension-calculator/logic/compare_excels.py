import pandas as pd

file1 = "document for upload pension piedad.xlsx"
file2 = "Pension document Fran.xlsx"

try:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    if df1.equals(df2):
        print("CONTENT_MATCH: Both files contain exactly the same data.")
    else:
        print("CONTENT_MISMATCH: The data in the files is different.")
        print("Diff:", df1.compare(df2))
except Exception as e:
    print(f"Error comparing files: {e}")
