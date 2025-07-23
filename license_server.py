from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import json
import os
import secrets
import string

app = Flask(__name__)

KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# ----------------- Utilities -----------------

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

def generate_key(length=25):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# ----------------- Routes -----------------

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

    # Bind HWID on first use
    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
        return jsonify({"status": "success", "message": "HWID bound"})

    # HWID mismatch
    if lic["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    # Check expiration
    if datetime.strptime(lic["expires"], "%Y-%m-%d") < datetime.now():
        return jsonify({"status": "error", "message": "License expired"}), 403

    return jsonify({"status": "success", "message": "Valid license"})

@app.route('/admin/list', methods=['GET', 'POST'])
def admin_panel():
    password = request.args.get("pw")
    if password != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()

    if request.method == 'POST' and request.form.get("action") == "generate":
        new_key = generate_key()
        keys[new_key] = {
            "hwid": "REPLACE_ME",
            "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
        save_keys(keys)

    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🔐 Admin Panel</title>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 30px;
        }
        h1 {
            color: #00ccff;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #1e1e1e;
        }
        th, td {
            border: 1px solid #333;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #222;
        }
        a {
            color: #ff5252;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        button {
            background-color: #00ccff;
            color: #000;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 15px;
        }
        button:hover {
            background-color: #0099cc;
        }
    </style>
</head>
<body>
    <h1>🔐 Admin Panel</h1>
    <form method="POST" style="margin-bottom: 20px;">
        <button type="submit" name="action" value="generate">+ Add Key</button>
    </form>
    <table>
        <tr>
            <th>Key</th>
            <th>HWID</th>
            <th>Expires</th>
            <th>Action</th>
        </tr>
        {% for key, data in keys.items() %}
        <tr>
            <td>{{ key }}</td>
            <td>{{ data["hwid"] }}</td>
            <td>{{ data["expires"] }}</td>
            <td><a href="/admin/delete/{{ key }}?pw={{ password }}">Delete</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
''', keys=keys, password=ADMIN_PASSWORD)

@app.route('/admin/delete/<key>')
def delete_key(key):
    password = request.args.get("pw")
    if password != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(f"/admin/list?pw={password}")

# ----------------- Run -----------------
if __name__ == '__main__':
    app.run(debug=True)

