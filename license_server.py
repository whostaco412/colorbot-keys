from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Load keys from file (you can also use a DB later)
with open("licenses.json", "r") as f:
    LICENSE_DB = json.load(f)

@app.route("/validate", methods=["POST"])
def validate_key():
    data = request.get_json()
    hwid = data.get("hwid")
    key = data.get("key")

    if not hwid or not key:
        return jsonify({"status": "error", "message": "Missing HWID or key"}), 400

    license_info = LICENSE_DB.get(key)
    if not license_info:
        return jsonify({"status": "invalid", "message": "Key not found"}), 403

    if license_info["hwid"] != hwid:
        return jsonify({"status": "invalid", "message": "HWID mismatch"}), 403

    if datetime.utcnow() > datetime.strptime(license_info["expires"], "%Y-%m-%d"):
        return jsonify({"status": "expired", "message": "License expired"}), 403

    return jsonify({"status": "valid", "message": "License valid"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
