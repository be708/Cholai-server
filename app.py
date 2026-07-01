from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
#import pandas as pd
import os
from difflib import get_close_matches
from datetime import datetime

app = Flask(_name_)
app.secret_key = os.environ.get("SECRET_KEY", "cholai_secret_key_change_me") # Change this on Render

CSV_PATH = 'data.csv'
ADMIN_LINK = 'cholai-admin-7749' # This is your private link. Don’t share it.
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Beverlyn2026") # Set this in Render ENV VARS

# Load dataset - DISABLED FOR TRIAL V1.0 NO pandas.
QUESTIONS = [
    
    "em i stap",
    "yu orait",
    "tenkyu tru",
    "cholai em wanem"
]
print(f"Cholai loaded: {len(QUESTIONS)} Q&A for trial")
    

# In-memory logs. For PNG scale this is ok. Later we add database.
CHAT_LOGS = [] # [time, ip, question, answer]

def find_answer(user_q):
    user_q = str(user_q).lower().strip()
    if not user_q: return "Susa, askim wanpla samting pastaim bestie."

    # Exact match first
    if user_q in QUESTIONS:
        return df[df['question'] == user_q]['answer'].iloc[0]

    # Fuzzy match for Tokpisin typos: "wanem" vs "wanem?"
    matches = get_close_matches(user_q, QUESTIONS, n=1, cutoff=0.75)
    if matches:
        return df[df['question'] == matches[0]]['answer'].iloc[0]

    return "Susa, mi no gat ansar lo dispela yet. Traim narapla askim o tok 'Halo'."

# === HTML TEMPLATE WITH STYLING ===
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cholai AI - PNG Tokpisin</title>
<style>
  :root{
    --bg:#000;
    --gold:#FFD700;
    --maroon:#800000;
    --maroon-hover:#A00000;
    --card:#111;
  }
  body{background:var(--bg); color:var(--gold); font-family:'Segoe UI', sans-serif; margin:0; padding:0;}
 .container{max-width:700px; margin:0 auto; padding:20px;}
  h1,h2,h3{color:var(--gold); text-align:center;}
 .chat-box{background:var(--card); border:1px solid var(--gold); border-radius:12px; padding:15px; min-height:300px; margin-bottom:15px; overflow-y:auto;}
 .msg-user{text-align:right; margin:8px 0; color:var(--gold);}
 .msg-bot{text-align:left; margin:8px 0; color:var(--gold);}
  input[type=text]{width:70%; padding:12px; border-radius:8px; border:1px solid var(--gold); background:#000; color:var(--gold); outline:none;}
  button{background:var(--maroon); color:var(--gold); border:none; padding:12px 18px; border-radius:8px; cursor:pointer; font-weight:bold;}
  button:hover{background:var(--maroon-hover);}
 .feedback{margin-top:10px; font-size:13px;}
 .feedback button{padding:6px 10px; font-size:12px; margin-right:6px;}
 .faq{display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px;}
 .faq button{width:100%; background:#222; border:1px solid var(--maroon);}
 .admin{background:#0a0a0a; border:1px solid var(--maroon); padding:15px; border-radius:10px; overflow-x:auto;}
  table{width:100%; border-collapse:collapse; color:var(--gold);}
  th,td{border:1px solid #333; padding:6px; font-size:13px; text-align:left;}
  a{color:var(--gold);}
 .footer{text-align:center; margin-top:20px; font-size:12px; opacity:0.8;}
</style>
</head>
<body>
<div class="container">
  <h1>🇵🇬 Cholai AI</h1>
  <p style="text-align:center;">Askim mi lo Tokpisin. Mi AI blo PNG.</p>

  {% if page == 'chat' %}
  <div class="chat-box" id="chatBox">
    {% for m in messages %}
      <div class="msg-{{m.role}}"><b>{{'Yu' if m.role=='user' else 'Cholai'}}:</b> {{m.text|safe}}</div>
    {% endfor %}
  </div>

  <form method="POST" action="/chat">
    <input type="text" name="q" placeholder="Raitim askim blo yu hia..." required autofocus>
    <button type="submit">Salim</button>
  </form>

  {% if last_answer %}
  <div class="feedback">
    <span>Dispela ansar i helpim yu?</span>
    <form style="display:inline" method="POST" action="/feedback">
      <input type="hidden" name="vote" value="yes">
      <button type="submit">👍 Yes</button>
    </form>
    <form style="display:inline" method="POST" action="/feedback">
      <input type="hidden" name="vote" value="no">
      <button type="submit">👎 No</button>
    </form>
  </div>
  {% endif %}

  <h3>Frequently Asked Questions</h3>
  <div class="faq">
    {% for q in faq %}
      <form method="POST" action="/chat"><button name="q" value="{{q}}">{{q}}</button></form>
    {% endfor %}
  </div>

  <div class="footer">
    <a href="/{{admin_link}}">Admin</a>
  </div>

  {% elif page == 'admin_login' %}
    <h2>Cholai Admin</h2>
    {% if error %}<p style="color:red; text-align:center;">{{error}}</p>{% endif %}
    <form method="POST" style="text-align:center;">
      <input type="password" name="pass" placeholder="Admin Password">
      <button type="submit">Enter</button>
    </form>

  {% elif page == 'admin' %}
    <h2>Dashboard - Chat Logs</h2>
    <p>Total Chats: {{logs|length}}</p>
    <div class="admin">
      <table>
        <tr><th>Time</th><th>IP</th><th>Question</th><th>Answer</th></tr>
        {% for t,ip,q,a in logs[-100:] %}
        <tr><td>{{t}}</td><td>{{ip}}</td><td>{{q}}</td><td>{{a[:80]}}...</td></tr>
        {% endfor %}
      </table>
    </div>
    <p style="text-align:center;"><a href="/">Back to Chat</a></p>
  {% endif %}
</div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    session.setdefault('messages', [])
    faq = df[df['tags']=='general']['question'].head(6).tolist() if 'tags' in df.columns else QUESTIONS[:6]
    return render_template_string(BASE_HTML, page='chat', messages=session['messages'], faq=faq, admin_link=ADMIN_LINK, last_answer=session.get('last_answer'))

@app.route('/chat', methods=['POST'])
def chat():
    q = request.form.get('q','')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) # Works on Render
    ans = find_answer(q)

    session['messages'] = session.get('messages', []) + [{'role':'user','text':q},{'role':'bot','text':ans}]
    session['last_answer'] = ans
    session.modified = True

    CHAT_LOGS.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, q, ans])
    return redirect(url_for('home'))

@app.route('/feedback', methods=['POST'])
def feedback():
    vote = request.form.get('vote')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    CHAT_LOGS.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, "FEEDBACK", vote])
    session['last_answer'] = None
    return redirect(url_for('home'))

@app.route(f'/{ADMIN_LINK}', methods=['GET','POST'])
def admin():
    if session.get('admin')!= True:
        if request.method == 'POST':
            if request.form.get('pass') == ADMIN_PASS:
                session['admin'] = True
                return redirect(url_for('admin'))
            return render_template_string(BASE_HTML, page='admin_login', error="Wrong password")
        return render_template_string(BASE_HTML, page='admin_login')
    return render_template_string(BASE_HTML, page='admin', logs=CHAT_LOGS)

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
