from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# File paths (in root of repo)
USERS_FILE = "users.json"
KEYS_FILE = "keys.json"
ONLINE_FILE = "online.json"
NOTIFICATIONS_FILE = "notifications.json"

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# --- API ENDPOINTS ---

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({"status": "ok"}), 200

@app.route('/api/version', methods=['GET'])
def api_version():
    return jsonify({"version": "1.0.0"}), 200

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users = load_json(USERS_FILE)
    for user in users:
        if user["username"] == username and user["password"] == password:
            return jsonify({"success": True, "user": user}), 200
    return jsonify({"success": False, "msg": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    key = data.get("product_key")
    users = load_json(USERS_FILE)

    if any(u["username"] == username for u in users):
        return jsonify({"success": False, "msg": "Username exists"}), 409

    # Optionally, validate product key
    if key:
        keys = load_json(KEYS_FILE)
        if key not in keys:
            return jsonify({"success": False, "msg": "Invalid product key"}), 400

    new_user = {"username": username, "password": password, "email": email, "product_key": key or ""}
    users.append(new_user)
    save_json(USERS_FILE, users)
    return jsonify({"success": True, "msg": "Account created"}), 201

@app.route('/api/notifications', methods=['GET', 'POST'])
def api_notifications():
    if request.method == 'GET':
        notifs = load_json(NOTIFICATIONS_FILE)
        return jsonify({"notifications": notifs}), 200
    else:
        data = request.get_json()
        message = data.get("message")
        if not message:
            return jsonify({"success": False, "msg": "No message"}), 400
        notifs = load_json(NOTIFICATIONS_FILE)
        notifs.append({"message": message})
        save_json(NOTIFICATIONS_FILE, notifs)
        return jsonify({"success": True, "msg": "Notification sent"}), 201

@app.route('/api/online', methods=['GET', 'POST'])
def api_online():
    if request.method == 'GET':
        online = load_json(ONLINE_FILE)
        return jsonify({"online": online}), 200
    else:
        data = request.get_json()
        username = data.get("username")
        if not username:
            return jsonify({"success": False, "msg": "Missing username"}), 400
        online = load_json(ONLINE_FILE)
        if username not in online:
            online.append(username)
            save_json(ONLINE_FILE, online)
        return jsonify({"success": True}), 200

@app.route('/', methods=['GET'])
def index():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
