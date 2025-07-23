from flask import Flask, request, jsonify, redirect, render_template_string
from datetime import datetime, timedelta
import json
import os
import secrets

app = Flask(__name__)

KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# Load and save functions
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# Routes
@app.route('/')
def index():
    return "License server running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing key or HWID"}), 400

    keys = load_keys()
    lic = keys.get(key)

    if not lic:
        return jsonify({"status": "error", "message": "Invalid key"}), 403

    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)

    if lic["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    if lic["expires"]:
        try:
            exp_date = datetime.strptime(lic["expires"], "%Y-%m-%dT%H:%M:%S")
            if datetime.utcnow() > exp_date:
                return jsonify({"status": "error", "message": "License expired"}), 403
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid expiration date format"}), 500

    return jsonify({"status": "success", "message": "License valid"}), 200

# Admin Panel
@app.route('/admin/list')
def list_keys():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    html = """
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            table { border-collapse: collapse; width: 100%; background: #fff; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #333; color: white; }
            h2 { margin-bottom: 10px; }
            button, input, select { padding: 6px; margin-right: 5px; }
            .delete { color: red; }
        </style>
    </head>
    <body>
        <h2>🔐 Admin Panel</h2>
        <form method="POST" action="/add">
            <input type="text" name="key" placeholder="Enter Key or Leave Empty for Random" size="50">
            <select name="duration">
                <option value="1d">1 Day</option>
                <option value="1m">1 Month</option>
                <option value="3m">3 Months</option>
                <option value="1y">1 Year</option>
                <option value="lifetime">Lifetime</option>
            </select>
            <button type="submit">+ Add Key</button>
        </form>
        <br/>
        <table>
            <tr><th>Key</th><th>HWID</th><th>Expires</th><th>Action</th></tr>
            {% for k, v in keys.items() %}
            <tr>
                <td>{{ k }}</td>
                <td>{{ v["hwid"] }}</td>
                <td>{{ v["expires"] or "Never" }}</td>
                <td><a class="delete" href="/delete?pw={{ pw }}&key={{ k }}">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, keys=keys, pw=request.args.get("pw"))

@app.route('/add', methods=['POST'])
def add_key():
    key = request.form.get("key") or secrets.token_hex(32)
    duration = request.form.get("duration")

    now = datetime.utcnow()
    if duration == "1d":
        expires = now + timedelta(days=1)
    elif duration == "1m":
        expires = now + timedelta(days=30)
    elif duration == "3m":
        expires = now + timedelta(days=90)
    elif duration == "1y":
        expires = now + timedelta(days=365)
    elif duration == "lifetime":
        expires = None
    else:
        expires = now + timedelta(days=30)  # Default

    keys = load_keys()
    keys[key] = {
        "hwid": "REPLACE_ME",
        "expires": None if expires is None else expires.strftime("%Y-%m-%dT%H:%M:%S")
    }

    save_keys(keys)
    return redirect("/admin/list?pw=" + ADMIN_PASSWORD)

@app.route('/delete')
def delete_key():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access Denied", 403

    key = request.args.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)

    return redirect("/admin/list?pw=" + ADMIN_PASSWORD)

# Run app
if __name__ == '__main__':
    app.run()
