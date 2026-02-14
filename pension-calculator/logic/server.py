from flask import Flask, request, jsonify, send_from_directory
import os
import tempfile
import json
from extract_semanas import extract_labor_history
import logging

app = Flask(__name__, static_folder='.')
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/upload_pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    print("DEBUG: Received Request - Method:", request.method)
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if 'file' not in request.files:
        print("DEBUG: No file in request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        print("DEBUG: Empty filename")
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            print(f"DEBUG: Saving file: {file.filename}")
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            
            print(f"DEBUG: Processing PDF at {tmp_path}")
            
            # Process (pdfplumber can sometimes hang on certain PDFs)
            import pdfplumber
            print("DEBUG: Opening PDF with pdfplumber...")
            with pdfplumber.open(tmp_path) as pdf:
                # Basic check to see if we can read it
                print(f"DEBUG: PDF has {len(pdf.pages)} pages")
                # full_text = "\n".join(p.extract_text() or "" for p in pdf.pages) # Optional skip if slow

            print("DEBUG: Calling extract_labor_history...")
            data = extract_labor_history(tmp_path, None)
            print(f"DEBUG: Extraction complete. Rows found: {len(data)}")
            
            # Cleanup
            os.remove(tmp_path)
            
            result = {'status': 'success', 'data': data}
            
            # Debug log to file
            with open('last_json_response.json', 'w') as jf:
                json.dump(result, jf, indent=2)
                
            return jsonify(result)
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            logging.error(f"Error processing PDF: {e}")
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Server on port 8080 (Threaded)...")
    app.run(port=8080, debug=False, threaded=True, host='0.0.0.0')
