from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
import secrets
import hashlib
import tempfile

# === CONFIG ===
app = Flask(__name__)

# Get Gemini key from env (Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD4n6Oj_RyjfQkm61RQwP0xEqnknJ4bKHI")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# In-memory license DB (upgrade to SQLite later)
LICENSES = {}

def generate_license(tier, phone):
    """Generate unique license key tied to phone + tier"""
    key = f"CLU-{secrets.token_hex(8).upper()}"
    expires_at = None
    if tier == "basic":
        expires_at = time.time() + 86400  # 1 day
    elif tier == "standard":
        expires_at = time.time() + 7 * 86400  # 7 days
    LICENSES[key] = {
        "tier": tier,
        "phone": phone,
        "used": False,
        "device_id": None,
        "expires_at": expires_at,
        "created_at": time.time()
    }
    return key

# === LICENSE ENDPOINTS ===

@app.route('/buy', methods=['POST'])
def buy_license():
    """Student pays → enters phone + amount → gets license key"""
    data = request.json
    phone = data.get('phone')
    amount = int(data.get('amount', 0))

    if not phone or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400

    # Auto-tier based on amount
    if amount >= 10000:
        tier = "premium"
    elif amount >= 5000:
        tier = "standard"
    else:
        tier = "basic"

    license_key = generate_license(tier, phone)
    return jsonify({"license_key": license_key, "tier": tier})

@app.route('/activate', methods=['POST'])
def activate_license():
    """Activate license key on device"""
    data = request.json
    license_key = data.get('license_key')
    device_id = data.get('device_id')  # HWID from Cluely.exe

    if not license_key or not device_id:
        return jsonify({"error": "Invalid request"}), 400

    if license_key not in LICENSES:
        return jsonify({"error": "Invalid license key"}), 401

    license_data = LICENSES[license_key]
    if license_data['used'] and license_data['device_id'] != device_id:
        return jsonify({"error": "License already activated on another device"}), 403

    # Activate
    LICENSES[license_key]['used'] = True
    LICENSES[license_key]['device_id'] = device_id
    LICENSES[license_key]['activated_at'] = time.time()

    return jsonify({
        "tier": license_data['tier'],
        "expires_at": license_data['expires_at'],
        "message": "License activated successfully"
    })

# === AI SOLVER ENDPOINT ===

@app.route('/solve', methods=['POST'])
def solve_exam():
    """AI exam solver with retry + error logging"""
    try:
        if 'screenshot' not in request.files:
            return jsonify({"answer": "No screenshot"}), 400
        
        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({"answer": "No selected file"}), 400
        
        # Use temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            file.save(tmp.name)
            
            try:
                myfile = genai.upload_file(tmp.name)
                
                # DYNAMIC PROMPT — HANDLES ALL QUESTION TYPES
                prompt = """
                You are a genius student taking an exam. The image shows a question.
                SOLVE IT STEP BY STEP if it's math/code. 
                If it's multiple choice — pick the correct letter (A, B, C, D).
                If it's history/biology — give a concise, accurate answer.
                If it's an essay — write a short, clear paragraph.
                RETURN ONLY THE FINAL ANSWER. NO EXPLANATION. BE 100% ACCURATE.
                """
                
                # RETRY 3 TIMES
                for attempt in range(3):
                    try:
                        response = model.generate_content([prompt, myfile])
                        if not response.parts:
                            raise ValueError("Gemini returned empty response")
                        
                        answer = response.text.strip()
                        os.unlink(tmp.name)
                        return jsonify({"answer": answer})
                    except Exception as e:
                        print(f"❌ [DEBUG] Gemini attempt {attempt+1} failed: {str(e)}", flush=True)
                        time.sleep(2)
                
                os.unlink(tmp.name)
                return jsonify({"answer": "Error. Try again later."}), 500
                
            except Exception as e:
                print(f"❌ [DEBUG] File upload error: {str(e)}", flush=True)
                os.unlink(tmp.name)
                return jsonify({"answer": "Error. Try again later."}), 500
                
    except Exception as e:
        print(f"❌ [DEBUG] Request error: {str(e)}", flush=True)
        return jsonify({"answer": "Error. Try again later."}), 500

# === RENDER CONFIG ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses PORT env var
    app.run(host='0.0.0.0', port=port, debug=False)  # MUST bind to 0.0.0.0=
