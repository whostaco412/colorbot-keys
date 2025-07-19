from flask import Flask, request, jsonify, render_template_string, redirect
from datetime import datetime, timedelta
import os, json, random, string

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, 'keys.json')
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "LuckyNumber9@18")

def load_keys():
    if not os.path.exists(KEY_FILE): return {}
    with open(KEY_FILE, 'r') as f: return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f: json.dump(keys, f, indent=4)

def generate_key(): return ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

def calc_exp(option):
    if option == "lifetime": return "lifetime"
    now = datetime.utcnow()
    durations = {
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "6mo": timedelta(days=180),
        "1yr": timedelta(days=365)
    }
    return (now + durations.get(option, timedelta(days=30))).isoformat()

@app.route('/')
def index(): return "License server running."

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    keys = load_keys()
    lic = keys.get(key)

    if not lic:
        return jsonify({"valid": False, "reason": "Invalid key"}), 403

    if lic["hwid"] in ["", "REPLACE_ME"]:
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "HWID mismatch"}), 403

    if lic["expires"] != "lifetime":
        try:
            if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
                return jsonify({"valid": False, "reason": "Expired"}), 403
        except:
            return jsonify({"valid": False, "reason": "Bad expiration format"}), 403

    return jsonify({"valid": True})

@app.route('/admin/list')
def admin_list():
    if request.args.get("pw") != ADMIN_PASSWORD: return "Access Denied", 403
    keys = load_keys()
    html = f"""
    <html><head><style>
    body {{ background:#111; color:#eee; font-family:Arial; }}
    table {{ border-collapse:collapse; width:100%; margin-top:20px; }}
    th,td {{ border:1px solid #444; padding:8px; }}
    </style></head><body>
    <h2>License Admin Panel</h2>
    <form method="post" action="/admin/add">
        <input type="hidden" name="pw" value="{ADMIN_PASSWORD}">
        <select name="type">
            <option value="30d">30d</option>
            <option value="90d">90d</option>
            <option value="6mo">6mo</option>
            <option value="1yr">1yr</option>
            <option value="lifetime">lifetime</option>
        </select>
        <button type="submit">+ Add Key</button>
    </form>
    <table><tr><th>Key</th><th>HWID</th><th>Expires</th><th>Delete</th></tr>
    """
    for k, v in keys.items():
        html += f"<tr><td>{k}</td><td>{v['hwid']}</td><td>{v['expires']}</td>" \
                f"<td><a href='/admin/delete/{k}?pw={ADMIN_PASSWORD}'>❌</a></td></tr>"
    html += "</table></body></html>"
    return html

@app.route('/admin/add', methods=['POST'])
def admin_add():
    if request.form.get("pw") != ADMIN_PASSWORD: return "Access Denied", 403
    key = generate_key()
    keys = load_keys()
    keys[key] = {"hwid": "REPLACE_ME", "expires": calc_exp(request.form.get("type", "30d"))}
    save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

@app.route('/admin/delete/<key>')
def admin_delete(key):
    if request.args.get("pw") != ADMIN_PASSWORD: return "Access Denied", 403
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(f"/admin/list?pw={ADMIN_PASSWORD}")

if __name__ == '__main__':
    app.run(debug=True)
