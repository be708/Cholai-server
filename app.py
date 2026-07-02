from flask import Flask, request, jsonify, render_template
from difflib import get_close_matches
import pandas as pd
import os

app = Flask(_name_)

# LOAD CSV - THIS IS THE FULL DATASET MODE
CSV_PATH = 'cholai_qa.csv'
df = pd.read_csv(CSV_PATH)
QA_LIST = df.to_dict('records')
print(f"Cholai loaded: {len(QA_LIST)} Q&A from CSV")

def find_answer(user_q):
    user_q = user_q.lower().strip()
    questions = [qa['question'].lower() for qa in QA_LIST]
    matches = get_close_matches(user_q, questions, n=1, cutoff=0.6)
    if matches:
        best_q = matches[0]
        for qa in QA_LIST:
            if qa['question'].lower() == best_q:
                return qa['answer']
    return "Mi no save yet Bestie. Trai narapela tok"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    answer = find_answer(user_message)
    return jsonify({'answer': answer})

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
