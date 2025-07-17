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
