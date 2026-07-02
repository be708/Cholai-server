import os
import pandas as pd
from flask import Flask, request, jsonify, render_template_string
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cholai_secret_key_change_me") # Change this on Render

# CONFIG
CSV_PATH = "cholai_qa.csv" # Must match your file name in repo ✅
ADMIN_LINK = "cholai-admin-7749" # This is your private link. Don't share it.
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Reverlyn2026") # Set this in Render ENV VARS

# LOAD DATASET ONCE WHEN APP STARTS
try:
    df = pd.read_csv(CSV_PATH)
    QUESTIONS = df.to_dict('records') # Converts CSV to list of dicts
    print(f"Cholai loaded: {len(QUESTIONS)} Q&A from CSV ✅")
except Exception as e:
    print(f"ERROR loading CSV: {e}")
    QUESTIONS = [] # Fallback so app doesn't crash

def get_best_answer(user_q):
    """Find closest match from CSV using difflib"""
    if not QUESTIONS:
        return "Sorry Bestie, my brain CSV isn't loaded yet 😭"
    
    questions_only = [q['question'] for q in QUESTIONS]
    matches = get_close_matches(user_q.lower(), questions_only, n=1, cutoff=0.6)
    
    if matches:
        best_match = matches[0]
        for q in QUESTIONS:
            if q['question'] == best_match:
                return q['answer']
    return "I don't have that yet Bestie. Ask me something else or tell the admin to add it 💬"

# ROUTES
@app.route("/")
def home():
    return render_template_string("""
    <h1>Cholai Bot is Live ✅</h1>
    <p>POST to /ask with json: {"question": "your question"}</p>
    """)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_q = data.get("question", "")
    answer = get_best_answer(user_q)
    return jsonify({"answer": answer})

@app.route(f"/{ADMIN_LINK}", methods=["GET", "POST"])
def admin():
    # Add your admin logic here later
    return "Admin panel. Set ADMIN_PASS in Render."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) # Render requires this
    app.run(host="0.0.0.0", port=port, debug=False) # 0.0.0.0 is required for Render
