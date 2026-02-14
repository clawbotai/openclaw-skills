import pypdf
import sys

def analyze(filename):
    print(f"--- Analyzing {filename} ---")
    try:
        reader = pypdf.PdfReader(filename)
        print(f"Metadata: {reader.metadata}")
        
        # Check fonts on first page
        if len(reader.pages) > 0:
            page = reader.pages[0]
            if '/Resources' in page and '/Font' in page['/Resources']:
                fonts = page['/Resources']['/Font']
                print(f"Fonts: {fonts.keys()}")
            
            # Extract text to guess layout
            text = page.extract_text()
            print("First 500 chars of text:")
            print(text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

analyze("Manuel_Velez_Resume.pdf")
analyze("Freelance Resume.pdf")
