from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

LICENSE_FILE = "licenses.json"
ADMIN_PASSWORD = "secret123"  # Change this to your own password

# Make sure license file exists
if not os.path.exists(LICENSE_FILE):
    with open(LICENSE_FILE, "w") as f:
        json.dump([], f)

def load_licenses():
    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def require_password(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method == "POST" and request.form.get("pw") != ADMIN_PASSWORD:
            return "Unauthorized (wrong password)", 401
        return f(*args, **kwargs)
    return wrapper

@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json(force=True)
    hwid = data.get("hwid")
    key = data.get("key")

    if not hwid or not key:
        return jsonify({"valid": False, "error": "Missing key or HWID"}), 400

    licenses = load_licenses()
    for lic in licenses:
        if lic["key"] == key and lic["hwid"] == hwid:
            if lic.get("expires"):
                try:
                    if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
                        return jsonify({"valid": False, "error": "Expired"}), 403
                except:
                    return jsonify({"valid": False, "error": "Invalid expiration format"}), 500
            return jsonify({"valid": True})

    return jsonify({"valid": False, "error": "Invalid license"}), 403

@app.route("/admin", methods=["GET", "POST"])
@require_password
def admin():
    if request.method == "POST":
        key = request.form.get("key")
        hwid = request.form.get("hwid")
        expires = request.form.get("expires")

        if not key or not hwid:
            return "Key and HWID required", 400

        licenses = load_licenses()
        licenses.append({
            "key": key,
            "hwid": hwid,
            "expires": expires if expires else None
        })
        save_licenses(licenses)

    html = '''
    <h2>License Admin Panel</h2>
    <form method="post">
        Password: <input type="password" name="pw"><br>
        Key: <input name="key"><br>
        HWID: <input name="hwid"><br>
        Expiration (optional ISO): <input name="expires" value="2025-07-30T00:00:00"><br>
        <input type="submit" value="Add Key">
    </form>
    '''
    return render_template_string(html)

if __name__ == "__main__":
    app.run()

