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

    from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json
import os

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

    # First-time HWID bind
    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
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
        hwid = request.form.get('hwid', 'REPLACE_ME')
        expires = request.form.get('expires')

        if not key:
            return "Missing key", 400

        keys = load_keys()
        keys[key] = {"hwid": hwid}
        if expires:
            keys[key]["expires"] = expires
        save_keys(keys)
        return render_template("admin_result.html", message="✅ Key added successfully!")

    return render_template("admin.html", pw=pw)

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
        return render_template("admin_result.html", message=f"🗑️ Key '{key}' deleted.")
    return render_template("admin_result.html", message="⚠️ Key not found.")

@app.route('/admin/list')
def list_keys():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    keys = load_keys()
    return render_template("list.html", keys=keys)

# Required for gunicorn
app = app

