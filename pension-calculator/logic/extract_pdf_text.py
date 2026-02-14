import pypdf

def extract_text(filename):
    print(f"--- Extracting text from {filename} ---")
    try:
        reader = pypdf.PdfReader(filename)
        for i, page in enumerate(reader.pages):
            print(f"--- Page {i+1} ---")
            print(page.extract_text())
    except Exception as e:
        print(f"Error: {e}")

extract_text("Manuel_Velez_Resume.pdf")
