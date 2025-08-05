from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import uuid
import time
from datetime import datetime, timedelta
from utils import load_json, save_json, generate_license_key, verify_admin_credentials
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Replace with secure key in production

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
KEYS_FILE = os.path.join(DATA_DIR, "keys.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")

# Ensure data directory and files exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
for file in [USERS_FILE, KEYS_FILE, NOTIFICATIONS_FILE]:
    if not os.path.exists(file):
        save_json(file, [])

# Admin login required decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if verify_admin_credentials(username, password):
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/admin", methods=["GET"])
@admin_login_required
def admin_panel():
    users = load_json(USERS_FILE)
    keys = load_json(KEYS_FILE)
    notifications = load_json(NOTIFICATIONS_FILE)
    return render_template("admin_panel.html", users=users, keys=keys, notifications=notifications)

@app.route("/admin/logout", methods=["POST"])
@admin_login_required
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/generate_key", methods=["POST"])
@admin_login_required
def generate_key():
    duration = request.form.get("duration")
    duration_seconds = {
        "24h": 86400,
        "1w": 604800,
        "1m": 2592000,
        "lifetime": None
    }.get(duration, 86400)
    
    key = generate_license_key()
    keys = load_json(KEYS_FILE)
    keys.append({
        "key": key,
        "active": False,
        "user": None,
        "created_at": int(time.time()),
        "expires_at": None if duration == "lifetime" else int(time.time()) + duration_seconds,
        "duration": duration
    })
    save_json(KEYS_FILE, keys)
    return redirect(url_for("admin_panel"))

@app.route("/admin/toggle_key/<key>", methods=["POST"])
@admin_login_required
def toggle_key(key):
    keys = load_json(KEYS_FILE)
    for k in keys:
        if k["key"] == key:
            k["active"] = not k["active"]
            if k["active"] and k["expires_at"]:
                k["expires_at"] = int(time.time()) + (86400 if k["duration"] == "24h" else 604800 if k["duration"] == "1w" else 2592000)
            elif not k["active"]:
                k["expires_at"] = None
    save_json(KEYS_FILE, keys)
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_key/<key>", methods=["POST"])
@admin_login_required
def delete_key(key):
    keys = load_json(KEYS_FILE)
    keys = [k for k in keys if k["key"] != key]
    save_json(KEYS_FILE, keys)
    return redirect(url_for("admin_panel"))

@app.route("/admin/assign_key", methods=["POST"])
@admin_login_required
def assign_key():
    username = request.form.get("username")
    key = request.form.get("key")
    users = load_json(USERS_FILE)
    keys = load_json(KEYS_FILE)
    for u in users:
        if u["username"] == username:
            u["license_key"] = key
    for k in keys:
        if k["key"] == key:
            k["user"] = username
    save_json(USERS_FILE, users)
    save_json(KEYS_FILE, keys)
    return redirect(url_for("admin_panel"))

@app.route("/admin/create_user", methods=["POST"])
@admin_login_required
def create_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    users = load_json(USERS_FILE)
    if any(u["username"] == username for u in users):
        return redirect(url_for("admin_panel"))
    users.append({
        "username": username,
        "email": email,
        "password": password,  # In production, hash passwords
        "license_key": None
    })
    save_json(USERS_FILE, users)
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_user/<username>", methods=["POST"])
@admin_login_required
def delete_user(username):
    users = load_json(USERS_FILE)
    keys = load_json(KEYS_FILE)
    users = [u for u in users if u["username"] != username]
    for k in keys:
        if k["user"] == username:
            k["user"] = None
    save_json(USERS_FILE, users)
    save_json(KEYS_FILE, keys)
    return redirect(url_for("admin_panel"))

@app.route("/admin/send_notification", methods=["POST"])
@admin_login_required
def send_notification():
    message = request.form.get("message")
    target = request.form.get("target")
    notifications = load_json(NOTIFICATIONS_FILE)
    notifications.append({
        "id": str(uuid.uuid4()),
        "message": message,
        "target": target if target != "all" else None,
        "created_at": int(time.time())
    })
    save_json(NOTIFICATIONS_FILE, notifications)
    return redirect(url_for("admin_panel"))

# API endpoints
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    key = data.get("key")
    users = load_json(USERS_FILE)
    keys = load_json(KEYS_FILE)
    user = next((u for u in users if u["username"] == username and u["license_key"] == key), None)
    key_data = next((k for k in keys if k["key"] == key), None)
    if not user or not key_data:
        return jsonify({"error": "Invalid username or license key"}), 401
    if not key_data["active"]:
        return jsonify({"error": "License key is inactive"}), 401
    if key_data["expires_at"] and key_data["expires_at"] < int(time.time()):
        return jsonify({"error": "License key has expired"}), 401
    return jsonify({"success": True, "username": username})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    key = data.get("key")
    users = load_json(USERS_FILE)
    keys = load_json(KEYS_FILE)
    if any(u["username"] == username for u in users):
        return jsonify({"error": "Username already exists"}), 400
    key_data = next((k for k in keys if k["key"] == key), None)
    if not key_data:
        return jsonify({"error": "Invalid license key"}), 400
    if key_data["user"]:
        return jsonify({"error": "License key already assigned"}), 400
    users.append({
        "username": username,
        "email": email,
        "password": password,  # In production, hash passwords
        "license_key": key
    })
    for k in keys:
        if k["key"] == key:
            k["user"] = username
    save_json(USERS_FILE, users)
    save_json(KEYS_FILE, keys)
    return jsonify({"success": True})

@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.get_json()
    username = data.get("username")
    notifications = load_json(NOTIFICATIONS_FILE)
    messages = [n["message"] for n in notifications if n["target"] in [username, None]]
    return jsonify({"messages": messages})

@app.route("/api/license_status", methods=["GET"])
def api_license_status():
    key = request.args.get("key")
    keys = load_json(KEYS_FILE)
    key_data = next((k for k in keys if k["key"] == key), None)
    if not key_data:
        return jsonify({"error": "Invalid license key"}), 400
    return jsonify({
        "active": key_data["active"],
        "expires_at": key_data["expires_at"],
        "user": key_data["user"],
        "duration": key_data["duration"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
