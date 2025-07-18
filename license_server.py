from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import json
import os
import uuid

app = Flask(__name__)
KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# Load and save
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# Helper: Expiration dates
def get_expiration(option):
    now = datetime.utcnow()
    if option == "30d":
        return (now + timedelta(days=30)).strftime("%Y-%m-%d")
    if option == "60d":
        return (now + timedelta(days=60)).strftime("%Y-%m-%d")
    if option == "90d":
        return (now + timedelta(days=90)).strftime("%Y-%m-%d")
    if option == "6mo":
        return (now + timedelta(days=182)).strftime("%Y-%m-%d")
    if option == "1yr":
        return (now + timedelta(days=365)).strftime("%Y-%m-%d")
    return "lifetime"

# Route: Verify
@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    keys = load_keys()
    lic = keys.get(key)
    if not lic:
        return jsonify({"valid": False})

    # HWID lock
    if lic["hwid"] == "":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False})

    # Check expiration
    if lic["expires"] != "lifetime":
        if datetime.utcnow().date() > datetime.strptime(lic["expires"], "%Y-%m-%d").date():
            return jsonify({"valid": False})

    return jsonify({"valid": True})

# Route: Admin Panel
@app.route('/admin/list')
def admin_list():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access Denied"
    keys = load_keys()
    html = """
    <html><head><title>Admin Panel</title>
    <style>
        body { background-color: #111; color: #eee; font-family: Arial; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: left; }
        th { background-color: #222; }
        a { color: #6cf; }
        input, select, button { margin: 5px; padding: 5px; }
    </style></head><body>
    <h2>🔐 License Admin Panel</h2>
    <form action="/admin/add" method="post">
        <input type="hidden" name="pw" value="{pw}">
        <select name="type">
            <option value="30d">30 Days</option>
            <option value="60d">60 Days</option>
            <option value="90d">90 Days</option>
            <option value="6mo">6 Months</option>
            <option value="1yr">1 Year</option>
            <option value="lifetime">Lifetime</option>
        </select>
        <button type="submit">+ Generate Key</button>
    </form>
    <table><tr><th>Key</th><th>HWID</th><th>Expires</th><th>Action</th></tr>
    """.format(pw=ADMIN_PASSWORD)

    for key, info in keys.items():
        html += f"<tr><td>{key}</td><td>{info['hwid']}</td><td>{info['expires']}</td>"
        html += f"<td><a href='/admin/delete?pw={ADMIN_PASSWORD}&key={key}'>Delete</a></td></tr>"
    html += "</table></body></html>"
    return html

# Route: Add Key
@app.route('/admin/add', methods=['POST'])
def admin_add():
    if request.form.get("pw") != ADMIN_PASSWORD:
        return "Access Denied"

    exp_option = request.form.get("type")
    expiration = get_expiration(exp_option)
    new_key = uuid.uuid4().hex

    keys = load_keys()
    keys[new_key] = {"hwid": "", "expires": expiration}
    save_keys(keys)

    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

# Route: Delete Key
@app.route('/admin/delete')
def admin_delete():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access Denied"

    key = request.args.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)

    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

# Health check
@app.route('/')
def index():
    return "License server is running."

if __name__ == "__main__":
    app.run(debug=True)
