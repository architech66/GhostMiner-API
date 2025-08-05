import json
import uuid
import string
import random

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def generate_license_key():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(16))

def verify_admin_credentials(username, password):
    # Replace with secure admin credentials check in production
    return username == "admin" and password == "admin123"
