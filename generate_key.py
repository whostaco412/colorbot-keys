import uuid
import json
from datetime import datetime, timedelta

# Generate random key
def generate_key():
    return str(uuid.uuid4()).replace('-', '')

# Save to JSON
def save_to_json(key, hwid="REPLACE_ME", days_valid=30):
    license_data = {
        key: {
            "hwid": hwid,
            "expires": (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
        }
    }

    try:
        with open("licenses.json", "r") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = {}

    existing.update(license_data)

    with open("licenses.json", "w") as f:
        json.dump(existing, f, indent=4)

    print(f"[+] Key generated and saved: {key}")

if __name__ == "__main__":
    new_key = generate_key()
    save_to_json(new_key)
