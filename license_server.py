from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import json
import os
import secrets

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

# Generate 64-character random license key
def generate_key():
    return secrets.token_hex(32)

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

    expiry = lic.get("expiry")
    if expiry:
        try:
            if datetime.strptime(expiry, "%Y-%m-%d") < datetime.today():
                return jsonify({"status": "error", "message": "Key expired"}), 403
        except:
            return jsonify({"status": "error", "message": "Invalid expiry format"}), 403

    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    return jsonify({"valid": True})

@app.route('/admin/list')
def admin_list():
    password = request.args.get("pw")
    if password != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()
    html = """
    <html>
    <head>
        <title>License Admin</title>
        <style>
            body { background-color: #111; color: #0ff; font-family: monospace; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; border: 1px solid #444; }
            th { background-color: #222; }
            td { background-color: #000; color: #ccc; }
            .delete { color: red; }
            .create-form { margin-top: 30px; }
        </style>
    </head>
    <body>
        <h1>Active License Keys</h1>
        <table>
            <tr><th>Key</th><th>HWID</th><th>Expiry</th><th>Action</th></tr>
            {% for key, info in keys.items() %}
            <tr>
                <td>{{ key }}</td>
                <td>{{ info["hwid"] }}</td>
                <td>{{ info.get("expiry", "None") }}</td>
                <td><a href="/admin/delete?pw={{ pw }}&key={{ key }}" class="delete">Delete</a></td>
            </tr>
            {% endfor %}
        </table>

        <div class="create-form">
            <h2>Create New Key</h2>
            <form action="/admin/create" method="post">
                <input type="hidden" name="pw" value="{{ pw }}">
                Key: <input type="text" name="key" id="keyInput" required>
                <button type="button" onclick="generateKey()">Generate</button>
                <br><br>
                Duration:
                <select name="preset">
                    <option value="">-- Select Duration --</option>
                    <option value="30">30 Days</option>
                    <option value="60">60 Days</option>
                    <option value="90">90 Days</option>
                    <option value="180">6 Months</option>
                    <option value="365">1 Year</option>
                    <option value="lifetime">Lifetime</option>
                </select>
                <br><br>
                OR Manual Expiry (YYYY-MM-DD): <input type="text" name="expiry">
                <br><br>
                <input type="submit" value="Add Key">
            </form>

            <script>
                function generateKey() {
                    fetch('/admin/genkey?pw={{ pw }}')
                        .then(response => response.text())
                        .then(key => document.getElementById('keyInput').value = key);
                }
            </script>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, keys=keys, pw=password)

@app.route('/admin/genkey')
def genkey():
    password = request.args.get("pw")
    if password != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()
    while True:
        key = generate_key()
        if key not in keys:
            return key

@app.route('/admin/create', methods=['POST'])
def create_key():
    password = request.form.get("pw")
    if password != ADMIN_PASSWORD:
        return "Access denied", 403

    key = request.form.get("key")
    manual_expiry = request.form.get("expiry")
    preset = request.form.get("preset")

    expiry = None

    if preset and preset != "lifetime":
        try:
            days = int(preset)
            expiry_date = datetime.today().date() + timedelta(days=days)
            expiry = expiry_date.strftime("%Y-%m-%d")
        except:
            expiry = None
    elif preset == "lifetime":
        expiry = None
    elif manual_expiry:
        expiry = manual_expiry

    keys = load_keys()
    keys[key] = {
        "hwid": "REPLACE_ME",
        "expiry": expiry
    }
    save_keys(keys)
    return redirect(f"/admin/list?pw={password}")

@app.route('/admin/delete')
def delete_key():
    password = request.args.get("pw")
    key = request.args.get("key")

    if password != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)

    return redirect(f"/admin/list?pw={password}")

if __name__ == '__main__':
    app.run(debug=True)
