from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json, os

app = Flask(__name__)

KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

@app.route('/')
def index():
    return "License server is running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    keys = load_keys()
    lic = keys.get(key)

    if not lic:
        return jsonify({"status": "error", "message": "Invalid key"}), 403

    if lic["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    if "expires" in lic and datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
        return jsonify({"status": "error", "message": "Key expired"}), 403

    return jsonify({"status": "success", "message": "License valid"})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    if request.method == 'POST':
        key = request.form.get('key')
        hwid = request.form.get('hwid')
        expires = request.form.get('expires')

        if not key or not hwid:
            return "Missing key or HWID", 400

        keys = load_keys()
        keys[key] = {"hwid": hwid}
        if expires:
            keys[key]["expires"] = expires
        save_keys(keys)
        return "Key added successfully."

    return render_template_string("""
    <html><head>
    <title>License Admin</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            padding: 20px;
        }
        input[type=text], input[type=datetime-local] {
            background-color: #1e1e1e;
            color: #fff;
            border: 1px solid #555;
            padding: 5px;
            width: 100%;
        }
        input[type=submit] {
            background-color: #03a9f4;
            color: white;
            padding: 8px 16px;
            border: none;
            cursor: pointer;
            margin-top: 10px;
        }
        a {
            color: #03a9f4;
        }
        .section {
            margin-bottom: 30px;
        }
    </style>
    </head><body>
        <h2>🔐 License Admin Panel</h2>

        <div class="section">
        <form method="post">
            <h3>➕ Add / Update Key</h3>
            Key: <input name="key" type="text"><br><br>
            HWID: <input name="hwid" type="text"><br><br>
            Expiration (ISO 8601): <input name="expires" type="text" placeholder="2025-12-31T23:59:59"><br><br>
            <input type="submit" value="Save Key">
        </form>
        </div>

        <div class="section">
        <form action="/admin/delete?pw={{pw}}" method="post">
            <h3>🗑️ Delete Key</h3>
            Key to Delete: <input name="key" type="text"><br><br>
            <input type="submit" value="Delete Key">
        </form>
        </div>

        <a href="/admin/list?pw={{pw}}">📜 View All Keys</a>
    </body></html>
    """, pw=pw)

@app.route('/admin/delete', methods=['POST'])
def delete_key():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    key = request.form.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        return f"Key '{key}' deleted."
    return "Key not found."

@app.route('/admin/list')
def list_keys():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    keys = load_keys()
    html = "<h2>All License Keys</h2><ul>"
    for k, v in keys.items():
        html += f"<li><b>{k}</b> - HWID: {v['hwid']} - Expires: {v.get('expires', 'None')}</li>"
    html += "</ul>"
    return html

# Needed for gunicorn
app = app
