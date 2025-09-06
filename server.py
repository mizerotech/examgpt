from flask import Flask, request, jsonify
import google.generativeai as genai

# STEP 1: Tell Flask to wake up
app = Flask(__name__)

# STEP 2: Give robot teacher a brain (Gemini AI)
genai.configure(api_key="AIzaSyDHYCHEqaQbu5CqxNN3ACLLKsjA1A6ILHU")  # Get free: aistudio.google.com
model = genai.GenerativeModel('gemini-1.5-flash')

# STEP 3: Robot’s job — solve exam questions
@app.route('/solve', methods=['POST'])
def solve_exam():
    # Student sends a photo of question
    question_photo = request.files['screenshot']
    question_photo.save("question.jpg")  # Save it like a picture on your phone
    
    # Robot teacher looks at photo + solves it
    myfile = genai.upload_file("question.jpg")
    prompt = "Solve this. Give ONLY final answer. No explanation. Be 100% accurate."
    answer = model.generate_content([prompt, myfile])
    
    # Robot sends answer back
    return jsonify({"answer": answer.text.strip()})

# STEP 4: Robot lives on internet (Render.com)
if __name__ == '__main__':
    app.run(debug=True)