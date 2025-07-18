# license_server.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime, timedelta
import json, os, random, string

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

# Generate a random key
def generate_random_key(length=64):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

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
        return jsonify({"valid": False, "message": "Invalid key"}), 403

    if lic.get("expiry"):
        if datetime.strptime(lic["expiry"], "%Y-%m-%d") < datetime.utcnow():
            return jsonify({"valid": False, "message": "Key expired"}), 403

    if lic.get("hwid") == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
    elif lic["hwid"] != hwid:
        return jsonify({"valid": False, "message": "HWID mismatch"}), 403

    return jsonify({"valid": True})

@app.route('/admin/list')
def admin_list():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Unauthorized", 403

    keys = load_keys()
    return render_template("admin.html", keys=keys, admin_password=ADMIN_PASSWORD)

@app.route('/delete', methods=['POST'])
def delete_key():
    if request.form.get("admin") != ADMIN_PASSWORD:
        return "Unauthorized", 403

    key = request.form.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(url_for('admin_list', pw=ADMIN_PASSWORD))

@app.route('/add', methods=['POST'])
def add_key():
    if request.form.get("admin") != ADMIN_PASSWORD:
        return "Unauthorized", 403

    duration = request.form.get("duration")
    if not duration:
        return "No duration provided", 400

    key = generate_random_key()
    now = datetime.utcnow()
    expiry = None

    if duration == "1d":
        expiry = now + timedelta(days=1)
    elif duration == "30d":
        expiry = now + timedelta(days=30)
    elif duration == "60d":
        expiry = now + timedelta(days=60)
    elif duration == "90d":
        expiry = now + timedelta(days=90)
    elif duration == "6m":
        expiry = now + timedelta(days=180)
    elif duration == "1y":
        expiry = now + timedelta(days=365)
    elif duration == "lifetime":
        expiry = None
    else:
        return "Invalid duration", 400

    keys = load_keys()
    keys[key] = {
        "hwid": "REPLACE_ME",
        "expiry": expiry.strftime("%Y-%m-%d") if expiry else None
    }
    save_keys(keys)

    return redirect(url_for('admin_list', pw=ADMIN_PASSWORD))

if __name__ == '__main__':
    app.run(debug=True)

