from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# Load keys from file
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

# Save keys to file
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

    if "expires" in lic:
        if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
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
        <h2>License Admin Panel</h2>
        <form method="post">
            <h3>Add / Update Key</h3>
            Key: <input name="key"><br>
            HWID: <input name="hwid"><br>
            Expiration (optional ISO): <input name="expires" value="2025-07-30T00:00:00"><br>
            <input type="submit" value="Add Key">
        </form>
        <hr>
        <form action="/admin/delete?pw={{pw}}" method="post">
            <h3>Delete Key</h3>
            Key to Delete: <input name="key"><br>
            <input type="submit" value="Delete Key">
        </form>
        <hr>
        <a href="/admin/list?pw={{pw}}">View All Keys</a>
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

@app.route('/admin/list', methods=['GET'])
def list_keys():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    keys = load_keys()
    html = "<h2>All License Keys</h2><ul>"
    for k, v in keys.items():
        html += f"<li><b>{k}</b> - HWID: {v['hwid']} - Expires: {v.get('expires', 'None')}</li>"
    html += "</ul>"
    html += f'<br><a href="/admin?pw={pw}">Back to Admin Panel</a>'
    return html

# Optional local testing
if __name__ == '__main__':
    app.run(debug=True)

