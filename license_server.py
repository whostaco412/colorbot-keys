from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

LICENSE_FILE = "licenses.json"
ADMIN_TOKEN = "LuckyNumber905162001"  # 🔐 Change this to something secure

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(licenses):
    with open(LICENSE_FILE, "w") as f:
        json.dump(licenses, f, indent=4)

def is_expired(expiration):
    if not expiration:
        return False
    return datetime.utcnow() > datetime.strptime(expiration, "%Y-%m-%d")

@app.route("/verify", methods=["POST"])
def verify_key():
    key = request.json.get("key")
    licenses = load_licenses()
    data = licenses.get(key)
    if data and not is_expired(data.get("expires")):
        return jsonify({"valid": True})
    return jsonify({"valid": False})

@app.route("/admin/keys", methods=["GET"])
def get_keys():
    if request.args.get("token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(load_licenses())

@app.route("/admin/add", methods=["POST"])
def add_key():
    if request.args.get("token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    key = request.json.get("key")
    expires = request.json.get("expires")  # Format: "YYYY-MM-DD"
    licenses = load_licenses()
    licenses[key] = {"expires": expires}
    save_licenses(licenses)
    return jsonify({"status": "added"})

@app.route("/admin/delete", methods=["POST"])
def delete_key():
    if request.args.get("token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    key = request.json.get("key")
    licenses = load_licenses()
    if key in licenses:
        del licenses[key]
        save_licenses(licenses)
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# For Railway / gunicorn to recognize this app
# DO NOT REMOVE THIS
app = app

