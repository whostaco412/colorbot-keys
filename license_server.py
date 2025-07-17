from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import hashlib
import os
import json

app = Flask(__name__)

KEY_FILE = "keys.json"
ADMIN_PASSWORD = "LuckyNumber9@18"

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f, indent=4)

def generate_key():
    return hashlib.sha256(os.urandom(32)).hexdigest()

@app.route("/")
def home():
    return "License server is running."

@app.route("/admin", methods=["GET", "POST"])
def admin():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 403

    if request.method == "POST":
        key = generate_key()
        hwid = request.form.get("hwid", "REPLACE_ME")
        days = int(request.form.get("days", 30))
        expiry = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
        keys = load_keys()
        keys[key] = {
            "hwid": hwid,
            "expiry": expiry
        }
        save_keys(keys)
        return render_template("admin_result.html", key=key, hwid=hwid, expiry=expiry)

    return render_template("admin.html")

@app.route("/admin/list")
def admin_list():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 403
    keys = load_keys()
    return render_template("list.html", keys=keys)

@app.route("/admin/delete/<key>", methods=["POST"])
def admin_delete(key):
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 403
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not found"})

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data.get("key", "")
    hwid = data.get("hwid", "")
    keys = load_keys()

    if key not in keys:
        return jsonify({"status": "invalid", "reason": "Key not found"})

    record = keys[key]
    expiry_date = datetime.strptime(record["expiry"], "%Y-%m-%d")
    if expiry_date < datetime.utcnow():
        return jsonify({"status": "invalid", "reason": "Key expired"})

    if record["hwid"] == "REPLACE_ME":
        # First use: lock the HWID
        record["hwid"] = hwid
        save_keys(keys)
    elif record["hwid"] != hwid:
        return jsonify({"status": "invalid", "reason": "HWID mismatch"})

    return jsonify({"status": "valid", "expires": record["expiry"]})

@app.route("/admin/delete", methods=["POST"])
def delete_key():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 403

    key_to_delete = request.form.get("key", "")
    keys = load_keys()

    if key_to_delete in keys:
        del keys[key_to_delete]
        save_keys(keys)
        return redirect(f"/admin/list?pw={pw}")
    return "Key not found", 404


if __name__ == "__main__":
    app.run(debug=True)

import hashlib
import os
import json
from datetime import datetime, timedelta

KEY_FILE = "keys.json"

# Load existing keys from file
def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return {}

# Save keys to file
def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# Generate secure key
def generate_key():
    return hashlib.sha256(os.urandom(32)).hexdigest()

# Add new key with predefined expiry option
def add_new_key(expiry_option="30d", hwid="REPLACE_ME"):
    days_map = {
        "30d": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "lifetime": None
    }

    if expiry_option not in days_map:
        print("❌ Invalid option. Use: 30d, 3m, 6m, 1y, or lifetime")
        return

    keys = load_keys()
    new_key = generate_key()

    if days_map[expiry_option] is None:
        expires = "lifetime"
    else:
        expires = (datetime.utcnow() + timedelta(days=days_map[expiry_option])).strftime("%Y-%m-%d")

    keys[new_key] = {
        "hwid": hwid,
        "expires": expires
    }

    save_keys(keys)
    print(f"✅ New key added:\nKEY: {new_key}\nHWID: {hwid}\nEXPIRES: {expires}")
    return new_key

# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    # Choose one of: "30d", "3m", "6m", "1y", "lifetime"
    add_new_key("30d")        # 30 days
    # add_new_key("3m")       # 3 months
    # add_new_key("6m")       # 6 months
    # add_new_key("1y")       # 1 year
    # add_new_key("lifetime") # no expiration

