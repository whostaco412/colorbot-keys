from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime, timedelta
import os
import json
import uuid
import secrets

app = Flask(__name__)
KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# --- Helpers ---
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

def generate_key():
    return secrets.token_hex(16)

def calculate_expiry(days):
    if days == "lifetime":
        return "lifetime"
    else:
        return (datetime.utcnow() + timedelta(days=int(days))).strftime("%Y-%m-%d")

# --- Routes ---
@app.route('/')
def index():
    return "License server running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get("key")
    hwid = data.get("hwid")

    keys = load_keys()
    lic = keys.get(key)

    if not lic:
        return jsonify({"valid": False}), 403

    # HWID lock
    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False}), 403

    # Expiry check
    if lic["expiry"] != "lifetime":
        if datetime.utcnow() > datetime.strptime(lic["expiry"], "%Y-%m-%d"):
            return jsonify({"valid": False}), 403

    return jsonify({"valid": True}), 200

# Admin Panel
@app.route('/admin/list')
def list_keys():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403
    return render_template("admin.html", keys=load_keys())

@app.route('/admin/add', methods=['POST'])
def add_key():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    expiry_days = request.form.get("expiry", "30")
    key = generate_key()

    keys = load_keys()
    keys[key] = {
        "hwid": "REPLACE_ME",
        "expiry": calculate_expiry(expiry_days)
    }
    save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

@app.route('/admin/delete', methods=['POST'])
def delete_key():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    key = request.form.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")
