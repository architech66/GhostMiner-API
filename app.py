import os, json
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

@app.route("/api/login", methods=["POST"])
def login():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username in users and check_password_hash(users[username], password):
        return jsonify({"success": True, "token": "FAKE_TOKEN"})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route("/api/add_user", methods=["POST"])
def add_user():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400
    if username in users:
        return jsonify({"success": False, "error": "User exists"}), 409
    users[username] = generate_password_hash(password)
    save_users(users)
    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
