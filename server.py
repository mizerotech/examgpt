from flask import Flask, request, jsonify
import os
import time
import secrets
import hashlib
import tempfile
import base64

# === DEEPSEEK IMPORT ===
from deepseek import DeepseekClient

app = Flask(__name__)

# === CONFIG ===
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-e96b9a4429b549a69c1da398b98af385")
client = DeepseekClient(api_key=DEEPSEEK_API_KEY)

# License DB
LICENSES = {}

def generate_license(tier, phone):
    key = f"CLU-{secrets.token_hex(8).upper()}"
    expires_at = None
    if tier == "basic":
        expires_at = time.time() + 86400
    elif tier == "standard":
        expires_at = time.time() + 7 * 86400
    LICENSES[key] = {
        "tier": tier,
        "phone": phone,
        "used": False,
        "device_id": None,
        "expires_at": expires_at,
    }
    return key

# === LICENSE ENDPOINTS ===

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
    return jsonify({
        "tier": license_data['tier'],
        "expires_at": license_data['expires_at'],
        "message": "License activated successfully"
    })

# === AI SOLVER WITH DEEPSEEK ===

@app.route('/solve', methods=['POST'])
def solve_exam():
    try:
        if 'screenshot' not in request.files:
            return jsonify({"answer": "No screenshot"}), 400
        
        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({"answer": "No selected file"}), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            file.save(tmp.name)
            
            try:
                # Read image as base64
                with open(tmp.name, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")
                
                # DeepSeek API call
                response = client.chat.completions.create(
                    model="deepseek-v3",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "You are a genius student taking an exam. The image shows a question. SOLVE IT STEP BY STEP if it's math/code. If it's multiple choice — pick the correct letter (A, B, C, D). If it's history/biology — give a concise, accurate answer. If it's an essay — write a short, clear paragraph. RETURN ONLY THE FINAL ANSWER. NO EXPLANATION. BE 100% ACCURATE."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                
                answer = response.choices[0].message.content.strip()
                os.unlink(tmp.name)
                return jsonify({"answer": answer})
                
            except Exception as e:
                print(f"❌ [DEBUG] DeepSeek error: {str(e)}", flush=True)
                os.unlink(tmp.name)
                return jsonify({"answer": "Error. Try again later."}), 500
                
    except Exception as e:
        print(f"❌ [DEBUG] Request error: {str(e)}", flush=True)
        return jsonify({"answer": "Error. Try again later."}), 500

# === RENDER CONFIG ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
