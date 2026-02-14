import sys
try:
    import pypdf
    print("pypdf available")
    # visual inspection logic here if needed
except ImportError:
    try:
        import PyPDF2
        print("PyPDF2 available")
    except ImportError:
        print("No PDF library found")
