from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import json
import os
import secrets

app = Flask(__name__)
KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# Load/save utils
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# License check API
@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    keys = load_keys()
    lic = keys.get(key)
    now = datetime.utcnow()

    if not lic:
        return jsonify({"valid": False, "reason": "invalid"}), 403

    # HWID check
    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "hwid_mismatch"}), 403

    # Expiration check
    if lic["expiry"] != "lifetime":
        exp = datetime.strptime(lic["expiry"], "%Y-%m-%d")
        if now > exp:
            return jsonify({"valid": False, "reason": "expired"}), 403

    return jsonify({"valid": True})

# Admin panel
@app.route('/admin/list')
def admin_list():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    html = """
    <html>
    <head>
        <title>License Admin</title>
        <style>
            body { background-color: #111; color: #0ff; font-family: Arial; }
            table, td, th { border: 1px solid #888; padding: 6px; border-collapse: collapse; }
            .btn { padding: 6px 10px; margin: 2px; }
            .delbtn { background-color: red; color: white; border: none; }
        </style>
    </head>
    <body>
        <h1>Active License Keys</h1>
        <table>
            <tr><th>Key</th><th>HWID</th><th>Expiry</th><th>Action</th></tr>
            {% for key, info in keys.items() %}
                <tr>
                    <td>{{ key }}</td>
                    <td>{{ info['hwid'] }}</td>
                    <td>{{ info['expiry'] }}</td>
                    <td>
                        <form action="/admin/delete" method="POST" style="display:inline;">
                            <input type="hidden" name="pw" value="{{ pw }}">
                            <input type="hidden" name="key" value="{{ key }}">
                            <button class="delbtn" type="submit">Delete</button>
                        </form>
                    </td>
                </tr>
            {% endfor %}
        </table>

        <h2>Add New Key</h2>
        <form action="/admin/add" method="POST">
            <input type="hidden" name="pw" value="{{ pw }}">
            <select name="duration">
                <option value="30">30 Days</option>
                <option value="60">60 Days</option>
                <option value="90">90 Days</option>
                <option value="180">6 Months</option>
                <option value="365">1 Year</option>
                <option value="lifetime">Lifetime</option>
            </select>
            <button type="sub
