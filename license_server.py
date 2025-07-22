from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime
import json
import os
import random
import string

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
    return "✅ License server is running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing key or HWID"}), 400

    keys = load_keys()
    if key not in keys:
        return jsonify({"status": "error", "message": "Invalid key"}), 403

    record = keys[key]

    if record["hwid"] == "REPLACE_ME":
        record["hwid"] = hwid  # auto bind
        save_keys(keys)

    if record["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    if datetime.strptime(record["expires"], "%Y-%m-%d") < datetime.now():
        return jsonify({"status": "error", "message": "Key expired"}), 403

    return jsonify({"status": "success", "message": "License valid"})

@app.route('/admin/list')
def admin_list():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    return render_template_string("""
        <h1>🔐 Admin Panel</h1>
        <a href="/admin/add?pw={{ pw }}"><button>+ Add Key</button></a>
        <table border="1" cellspacing="0" cellpadding="6">
            <tr><th>Key</th><th>HWID</th><th>Expires</th><th>Action</th></tr>
            {% for k, v in keys.items() %}
                <tr>
                    <td>{{ k }}</td>
                    <td>{{ v['hwid'] }}</td>
                    <td>{{ v['expires'] }}</td>
                    <td><a href="/admin/delete/{{ k }}?pw={{ pw }}">Delete</a></td>
                </tr>
            {% endfor %}
        </table>
    """, keys=keys, pw=pw)

@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Access Denied", 403

    if request.method == "POST":
        key = request.form.get("key")
        expires = request.form.get("expires")
        if not key:
            key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=48))
        keys = load_keys()
        keys[key] = {
            "hwid": "REPLACE_ME",
            "expires": expires
        }
        save_keys(keys)
        return redirect(f"/admin/list?pw={pw}")

    return render_template_string("""
        <h2>Add New Key</h2>
        <form method="post">
            Key (leave blank to auto-generate):<br>
            <input type="text" name="key"><br><br>
            Expiration Date (YYYY-MM-DD):<br>
            <input type="text" name="expires"><br><br>
            <input type="submit" value="Add Key">
        </form>
        <br>
        <a href="/admin/list?pw={{ pw }}">← Back to List</a>
    """, pw=pw)

@app.route("/admin/delete/<key>")
def admin_delete(key):
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(f"/admin/list?pw={pw}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
