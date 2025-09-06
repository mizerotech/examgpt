from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Get Gemini key from env (Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDHYCHEqaQbu5CqxNN3ACLLKsjA1A6ILHU")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/solve', methods=['POST'])
def solve_exam():
    try:
        if 'screenshot' not in request.files:
            return jsonify({"answer": "No screenshot"}), 400
        
        file = request.files['screenshot']
        file.save("question.jpg")
        
        myfile = genai.upload_file("question.jpg")
        prompt = "Solve this. Return ONLY final answer. No explanation."
        response = model.generate_content([prompt, myfile])
        
        return jsonify({"answer": response.text.strip()})
    except Exception as e:
        print("Server error:", str(e))
        return jsonify({"answer": "Error. Try again."})

# === CRITICAL: Bind to 0.0.0.0 + PORT for Render ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses PORT env var
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
