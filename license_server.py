from flask import Flask, request, jsonify, render_template_string, abort
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
KEY_FILE = "keys.json"
ADMIN_PASSWORD = "LuckyNumber9@18"  # Change this

# Load or initialize keys
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        licenses = json.load(f)
else:
    licenses = {}

# Save helper
def save_keys():
    with open(KEY_FILE, "w") as f:
        json.dump(licenses, f, indent=4)

# === Admin Auth Decorator ===
def require_password(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated

# === LICENSE CHECK ===
@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()
    if not data or "key" not in data or "hwid" not in data:
        return jsonify({"error": "Invalid request"}), 400

    key = data["key"]
    hwid = data["hwid"]
    lic = licenses.get(key)

    if not lic or lic["hwid"] != hwid:
        return jsonify({"valid": False}), 403

    # Check expiration
    if "expires" in lic and lic["expires"]:
        try:
            exp = datetime.fromisoformat(lic["expires"])
            if exp < datetime.utcnow():
                return jsonify({"valid": False, "error": "Expired"}), 403
        except Exception:
            return jsonify({"error": "Invalid expiration format"}), 500

    return jsonify({"valid": True})

# === ADMIN PANEL ===
@app.route("/admin", methods=["GET", "POST"])
@require_password
def admin():
    if request.method == "POST":
        key = request.form.get("key")
        hwid = request.form.get("hwid")
        exp = request.form.get("expires")

        if not key or not hwid:
            return "Missing key or HWID", 400

        licenses[key] = {
            "hwid": hwid,
            "expires": exp if exp else None
        }
        save_keys()
        return "Key added successfully."

    return render_template_string('''
        <h2>License Admin Panel</h2>
        <form method="post">
            Key: <input name="key"><br>
            HWID: <input name="hwid"><br>
            Expiration (optional ISO): <input name="expires"><br>
            <input type="submit" value="Add Key">
        </form>
    ''')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

