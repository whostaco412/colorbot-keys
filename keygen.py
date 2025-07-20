import uuid
import random
import string
import json
from datetime import datetime

LICENSES_FILE = "keys.json"  # ✅ Match server's expected filename

def generate_license_key():
    return '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(3))

def get_hwid():
    return str(uuid.UUID(int=uuid.getnode()))

def load_licenses():
    try:
        with open(LICENSES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_licenses(licenses):
    with open(LICENSES_FILE, "w") as f:
        json.dump(licenses, f, indent=4)

def write_key_file(key, path="license.key"):
    with open(path, "w") as f:
        f.write(key)

def main():
    hwid = get_hwid()
    print(f"🔍 Detected HWID: {hwid}")
    expires = input("📅 Enter expiration date (YYYY-MM-DD): ")

    try:
        datetime.strptime(expires, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return

    licenses = load_licenses()
    key = generate_license_key()

    licenses[key] = {
        "hwid": hwid,
        "expires": expires
    }

    save_licenses(licenses)
    write_key_file(key)

    print(f"\n✅ License Key Generated: {key}")
    print("📦 Saved to: keys.json")
    print("📝 Written to: license.key")

if __name__ == "__main__":
    main()
