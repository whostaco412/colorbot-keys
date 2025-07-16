from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

LICENSE_FILE = "keys.json"
ADMIN_PASSWORD = "LuckyNumber9@18"  # Update to your own password if needed


# --------------------------
# License Verification Route
# --------------------------
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.get_json()
        key = data.get("key")
        hwid = data.get("hwid")

        with open(LICENSE_FILE, "r") as f:
            licenses = json.load(f)

        for lic in licenses:
            if lic["key"] == key and lic["hwid"] == hwid:
                # Optional expiration check
                exp = lic.get("expiration")
                if exp:
                    try:
                        exp_time = datetime.fromisoformat(exp)
                        if datetime.utcnow() > exp_time:
                            return jsonify({"status": "expired"})
                    except ValueError:
                        return jsonify({"status": "error", "reason": "bad_expiration_format"})
                return jsonify({"status": "valid"})

        return jsonify({"status": "invalid"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# --------------------------
# Admin Panel (Add Keys)
# --------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Access denied", 403

    if request.method == "POST":
        key = request.form.get("key")
        hwid = request.form.get("hwid")
        expiration = request.form.get("expiration")

        # Load or initialize license data
        try:
            with open(LICENSE_FILE, "r") as f:
                licenses = json.load(f)
        except Exception:
            licenses = []

        new_entry = {"key": key, "hwid": hwid}
        if expiration:
            new_entry["expiration"] = expiration

        licenses.append(new_entry)

        with open(LICENSE_FILE, "w") as f:
            json.dump(licenses, f, indent=4)

        return redirect("/admin?pw=" + ADMIN_PASSWORD)

    # Render HTML form
    html = """
    <h2>License Admin Panel</h2>
    <form method="post">
        Key: <input name="key"><br>
        HWID: <input name="hwid"><br>
        Expiration (optional ISO): <input name="expiration" value="{default_exp}"><br>
        <button type="submit">Add Key</button>
    </form>
    """
    default_exp = datetime.utcnow().replace(microsecond=0).isoformat()
    return render_template_string(html.format(default_exp=default_exp))


# --------------------------
# Run Locally (optional)
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
