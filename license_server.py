from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)

LICENSE_FILE = "licenses.json"

# Load licenses from file
def load_licenses():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            return json.load(f)
    return []

# Save licenses to file
def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Route: License Validation
@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()
    hwid = data.get("hwid")
    key = data.get("key")
    licenses = load_licenses()

    for lic in licenses:
        if lic["key"] == key and lic["hwid"] == hwid:
            expires = lic.get("expires")
            if expires:
                if datetime.utcnow() > datetime.fromisoformat(expires):
                    return jsonify({"valid": False, "reason": "expired"})
            return jsonify({"valid": True})

    return jsonify({"valid": False, "reason": "invalid"})

# Route: Admin Page
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        key = request.form["key"]
        hwid = request.form["hwid"]
        expires = request.form.get("expires", "")

        licenses = load_licenses()
        licenses.append({
            "key": key,
            "hwid": hwid,
            "expires": expires if expires else None
        })
        save_licenses(licenses)

    return render_template_string("""
        <h2>License Admin Panel</h2>
        <form method="post">
            <label>Key: <input name="key"></label><br>
            <label>HWID: <input name="hwid"></label><br>
            <label>Expiration (optional ISO): <input name="expires" placeholder="2025-07-30T00:00:00"></label><br>
            <button type="submit">Add Key</button>
        </form>
    """)

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
