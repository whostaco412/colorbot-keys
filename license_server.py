from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import os, json, random, string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, 'keys.json')
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "LuckyNumber9@18")

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)
    print("[DEBUG] Keys saved.")

def generate_key():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

def calc_expiration(option):
    now = datetime.utcnow()
    if option == 'lifetime':
        return 'lifetime'
    days = {
        '30d': 30, '60d': 60, '90d': 90, '6mo': 182, '1yr': 365
    }.get(option, 30)
    return (now + timedelta(days=days)).isoformat()

@app.route('/')
def index():
    return "License server running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key, hwid = data.get("key"), data.get("hwid")
    keys = load_keys()
    lic = keys.get(key)

    if not lic:
        return jsonify({"valid": False, "reason": "Invalid key"}), 403

    if not lic.get("hwid") or lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "HWID mismatch"}), 403

    if lic["expires"] != "lifetime":
        try:
            if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
                return jsonify({"valid": False, "reason": "Key expired"}), 403
        except:
            return jsonify({"valid": False, "reason": "Invalid expiration format"}), 403

    return jsonify({"valid": True})

@app.route('/admin/list')
def admin_list():
    if request.args.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403
    keys = load_keys()
    html = f"""<html><head><style>
    body {{ background:#111; color:#eee; font-family:Arial }}
    table {{ width:100%; border-collapse: collapse }}
    th, td {{ border: 1px solid #333; padding: 8px }}
    a {{ color: #6cf }}
    </style></head><body>
    <h2>🔐 Admin Panel</h2>
    <form action="/admin/add" method="post">
    <input type="hidden" name="pw" value="{ADMIN_PASSWORD}">
    <select name="type">
        <option value="30d">30 Days</option><option value="60d">60 Days</option>
        <option value="90d">90 Days</option><option value="6mo">6 Months</option>
        <option value="1yr">1 Year</option><option value="lifetime">Lifetime</option>
    </select>
    <button type="submit">+ Add Key</button></form>
    <table><tr><th>Key</th><th>HWID</th><th>Expires</th><th>Action</th></tr>"""
    for k, v in keys.items():
        html += f"<tr><td>{k}</td><td>{v.get('hwid','')}</td><td>{v.get('expires')}</td><td><a href='/admin/delete/{k}?pw={ADMIN_PASSWORD}'>Delete</a></td></tr>"
    html += "</table></body></html>"
    return html

@app.route('/admin/add', methods=['POST'])
def admin_add():
    if request.form.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403
    key = generate_key()
    expires = calc_expiration(request.form.get("type", "30d"))
    keys = load_keys()
    keys[key] = {"hwid": "REPLACE_ME", "expires": expires}
    save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

@app.route('/admin/delete/<key>')
def admin_delete(key):
    if request.args.get('pw') != ADMIN_PASSWORD:
        return "Access Denied", 403
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

# 🚀 FIX FOR RENDER HOSTING — use assigned PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Fallback to 10000 locally
    app.run(host='0.0.0.0', port=port)
