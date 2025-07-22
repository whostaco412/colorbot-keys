from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)
KEY_FILE = 'keys.json'
ADMIN_PASSWORD = "LuckyNumber9@18"

# ----------------- Utility Functions -----------------

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# ----------------- Routes -----------------

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
        return jsonify({"status": "error", "message": "Invalid key"}), 403

    # Auto-bind if not bound yet
    if lic["hwid"] == "REPLACE_ME":
        lic["hwid"] = hwid
        save_keys(keys)
        return jsonify({"status": "success", "message": "HWID bound"}), 200

    if lic["hwid"] != hwid:
        return jsonify({"status": "error", "message": "HWID mismatch"}), 403

    if datetime.now() > datetime.strptime(lic["expires"], "%Y-%m-%d"):
        return jsonify({"status": "error", "message": "Key expired"}), 403

    return jsonify({"status": "success", "message": "Key valid"}), 200

@app.route('/admin/list')
def admin_list():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()

    html = """
    <h2>🔐 Admin Panel</h2>
    <form action="/admin/add" method="post">
        Key: <input name="key">
        Expire (YYYY-MM-DD): <input name="expires">
        <button type="submit">Add</button>
    </form>
    <table border="1">
        <tr><th>Key</th><th>HWID</th><th>Expires</th><th>Action</th></tr>
        {% for k, v in keys.items() %}
        <tr>
            <td>{{k}}</td>
            <td>{{v['hwid']}}</td>
            <td>{{v['expires']}}</td>
            <td><a href="/admin/delete?pw={{pw}}&key={{k}}">Delete</a></td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, keys=keys, pw=request.args.get("pw"))

@app.route('/admin/add', methods=["POST"])
def admin_add():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()
    key = request.form["key"]
    expires = request.form["expires"]
    keys[key] = {
        "hwid": "REPLACE_ME",
        "expires": expires
    }
    save_keys(keys)
    return "Key added. <a href='/admin/list?pw=" + ADMIN_PASSWORD + "'>Back</a>"

@app.route('/admin/delete')
def admin_delete():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    keys = load_keys()
    key = request.args.get("key")
    if key in keys:
        del keys[key]
        save_keys(keys)
    return "Key deleted. <a href='/admin/list?pw=" + ADMIN_PASSWORD + "'>Back</a>"

# ----------------- Start App -----------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

