
from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Get Gemini key — DO NOT EXIT ON ERROR
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ [DEBUG] WARNING: GEMINI_API_KEY not set in environment!", flush=True)
    # Do NOT exit — let server start → return error on /solve

try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ [DEBUG] Gemini configured successfully", flush=True)
    else:
        model = None
        print("⚠️ [DEBUG] Gemini not configured — will return errors", flush=True)
except Exception as e:
    print(f"❌ [DEBUG] Gemini configuration failed: {str(e)}", flush=True)
    model = None

@app.route('/solve', methods=['POST'])
def solve_exam():
    if not model:
        return jsonify({"answer": "Server misconfigured. Contact admin."}), 500

    try:
        print("📥 [DEBUG] Received request", flush=True)
        if 'screenshot' not in request.files:
            return jsonify({"answer": "No screenshot"}), 400
        
        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({"answer": "No selected file"}), 400
        
        # Use temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            file.save(tmp.name)
            print(f"💾 [DEBUG] Saved to temp file: {tmp.name}", flush=True)
            
            myfile = genai.upload_file(tmp.name)
            prompt = "Solve this. Return ONLY final answer. No explanation."
            response = model.generate_content([prompt, myfile])
            
            os.unlink(tmp.name)
            print(f"🤖 [DEBUG] AI Answer: {response.text.strip()}", flush=True)
            return jsonify({"answer": response.text.strip()})
    except Exception as e:
        print(f"❌ [DEBUG] Request error: {str(e)}", flush=True)
        return jsonify({"answer": "Error. Try again later."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🔌 [DEBUG] Starting server on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port, debug=False)
