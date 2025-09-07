from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
import secrets
import hashlib

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDHYCHEqaQbu5CqxNN3ACLLKsjA1A6ILHU")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

LICENSES = {}

def generate_license(tier, phone):
    key = f"CLU-{secrets.token_hex(8).upper()}"
    expires_at = None
    if tier == "basic":
        expires_at = time.time() + 86400
    elif tier == "standard":
        expires_at = time.time() + 7 * 86400
    LICENSES[key] = {"tier": tier, "phone": phone, "used": False, "device_id": None, "expires_at": expires_at}
    return key

@app.route('/buy', methods=['POST'])
def buy_license():
    data = request.json
    phone = data.get('phone')
    amount = int(data.get('amount', 0))
    if not phone or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400
    tier = "premium" if amount >= 10000 else "standard" if amount >= 5000 else "basic"
    license_key = generate_license(tier, phone)
    return jsonify({"license_key": license_key, "tier": tier})

@app.route('/activate', methods=['POST'])
def activate_license():
    data = request.json
    license_key = data.get('license_key')
    device_id = data.get('device_id')
    if not license_key or not device_id:
        return jsonify({"error": "Invalid request"}), 400
    if license_key not in LICENSES:
        return jsonify({"error": "Invalid license key"}), 401
    license_data = LICENSES[license_key]
    if license_data['used'] and license_data['device_id'] != device_id:
        return jsonify({"error": "License already activated on another device"}), 403
    LICENSES[license_key]['used'] = True
    LICENSES[license_key]['device_id'] = device_id
    return jsonify({"tier": license_data['tier'], "expires_at": license_data['expires_at'], "message": "License activated"})

@app.route('/solve', methods=['POST'])
def solve_exam():
    try:
        if 'screenshot' not in request.files:
            return jsonify({"answer": "No screenshot"}), 400
        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({"answer": "No selected file"}), 400
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            file.save(tmp.name)
            myfile = genai.upload_file(tmp.name)
            prompt = "Solve this. Return ONLY final answer. No explanation."
            for attempt in range(3):
                try:
                    response = model.generate_content([prompt, myfile])
                    if not response.parts:
                        raise ValueError("Empty response")
                    answer = response.text.strip()
                    os.unlink(tmp.name)
                    return jsonify({"answer": answer})
                except Exception as e:
                    print(f"❌ [DEBUG] Gemini attempt {attempt+1} failed: {str(e)}", flush=True)
                    time.sleep(2)
            os.unlink(tmp.name)
            return jsonify({"answer": "Error. Try again later."}), 500
    except Exception as e:
        print(f"❌ [DEBUG] Request error: {str(e)}", flush=True)
        return jsonify({"answer": "Error. Try again later."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)