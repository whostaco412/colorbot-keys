from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import os
import json
import random
import string

app = Flask(__name__)

# Absolute path to ensure keys.json always saves/loads correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, 'keys.json')
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "defaultpass")


def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)


def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)
    print("[DEBUG] Keys saved to", KEY_FILE)


def generate_key():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))


def calc_expiration(option):
    now = datetime.utcnow()
    durations = {
        '30d': timedelta(days=30),
        '60d': timedelta(days=60),
        '90d': timedelta(days=90),
        '6mo': timedelta(days=182),
        '1yr': timedelta(days=365),
        'lifetime': None
    }
    if option == 'lifetime':
        return 'lifetime'
    return (now + durations.get(option, timedelta(days=30))).isoformat()


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
        return jsonify({"valid": False, "reason": "Invalid key"}), 403

    # Auto-bind HWID
    if not lic.get("hwid") or lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "HWID mismatch"}), 403

    # Expiration check
    if lic["expires"] != "lifetime":
        try:
            if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
                return jsonify({"valid": False, "reason": "Key expired"}), 403
        except Exception:
            return jsonify({"valid": False, "reason": "Invalid expiration format"}), 403

    return jsonify({"valid": True})


@app.route('/admin/list')
def admin_list():
    if request.args.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    html = f"""
    <html><head><title>Admin Panel</title>
    <style>
        body {{ background-color: #111; color: #eee; font-family: Arial; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
        th {{ background-color: #222; }}
        a {{ color: #6cf; }}
        input, select, button {{ margin: 5px; padding: 5px; }}
    </style></head><body>
    <h2>🔐 License Admin Panel</h2>
    <form action="/admin/add" method="post">
        <input type="hidden" name="pw" value="{ADMIN_PASSWORD}">
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
    """
    for k, v in keys.items():
        html += f"<tr><td>{k}</td><td>{v.get('hwid', '')}</td><td>{v.get('expires', '')}</td><td><a href='/admin/delete/{k}?pw={ADMIN_PASSWORD}'>Delete</a></td></tr>"
    html += "</table></body></html>"
    return html


@app.route('/admin/add', methods=['POST'])
def admin_add():
    if request.form.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403

    duration = request.form.get('type', '30d')
    key = generate_key()
    expires = calc_expiration(duration)

    keys = load_keys()
    keys[key] = {"hwid": "REPLACE_ME", "expires": expires}
    save_keys(keys)
    print(f"[DEBUG] Generated key {key} ({duration})")
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")


@app.route('/admin/delete/<key>')
def admin_delete(key):
    if request.args.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403

    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        print(f"[DEBUG] Deleted key {key}")
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")


if __name__ == '__main__':
    app.run(debug=True)
