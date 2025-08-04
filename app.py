import os, json, time, secrets
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-key")

USER_FILE = "users.json"
KEY_FILE = "keys.json"
ONLINE_FILE = "online.json"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

# --- Models ---
def load_users():
    return load_json(USER_FILE, {})

def save_users(users):
    save_json(USER_FILE, users)

def load_keys():
    return load_json(KEY_FILE, {})

def save_keys(keys):
    save_json(KEY_FILE, keys)

def load_online():
    return load_json(ONLINE_FILE, {})

def save_online(online):
    save_json(ONLINE_FILE, online)

# --- Utility ---
def require_admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

# --- Web: Admin Login & Dashboard ---
@app.route("/")
def root():
    return redirect(url_for("admin_login"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        user = users.get(username)
        if user and check_password_hash(user["password"], password) and user.get("is_admin"):
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    users = load_users()
    online = load_online()
    keys = load_keys()
    return render_template("dashboard.html", users=users, online=online, keys=keys)

@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    users = load_users()
    username = request.form.get("username")
    password = request.form.get("password")
    is_admin = request.form.get("is_admin") == "on"
    email = request.form.get("email")
    key = request.form.get("key", "")
    if not username or not password:
        return redirect(url_for("admin_dashboard"))
    if username in users:
        return redirect(url_for("admin_dashboard"))
    users[username] = {
        "password": generate_password_hash(password),
        "is_admin": is_admin,
        "email": email,
        "product_key": key
    }
    save_users(users)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/remove_user/<username>")
def admin_remove_user(username):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
    return redirect(url_for("admin_dashboard"))

# --- Web: Product Key Management ---
@app.route("/admin/keys", methods=["GET", "POST"])
def admin_keys():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    keys = load_keys()
    if request.method == "POST":
        # Generate a new key
        category = request.form.get("category", "default")
        duration = int(request.form.get("duration", 30))
        key = secrets.token_hex(8).upper()  # 16 hex chars
        keys[key] = {
            "category": category,
            "duration": duration,
            "created": int(time.time()),
            "assigned_user": "",
            "active": True
        }
        save_keys(keys)
    return render_template("keys.html", keys=keys)

@app.route("/admin/deactivate_key/<key>")
def admin_deactivate_key(key):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    keys = load_keys()
    if key in keys:
        keys[key]["active"] = False
        save_keys(keys)
    return redirect(url_for("admin_keys"))

# --- API: Client/Front-End routes ---
@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

@app.route("/api/login", methods=["POST"])
def login():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user = users.get(username)
    if user and check_password_hash(user["password"], password):
        # Record "online"
        online = load_online()
        online[username] = {
            "last_seen": time.time(),
            "ip": request.remote_addr
        }
        save_online(online)
        return jsonify({"success": True, "token": "FAKE_TOKEN", "product_key": user.get("product_key", "")})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route("/api/register", methods=["POST"])
def api_register():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    product_key = data.get("product_key", "")
    if not username or not password or not email:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    if username in users:
        return jsonify({"success": False, "error": "Username already exists"}), 409
    # Validate key if provided
    keys = load_keys()
    if product_key:
        key_data = keys.get(product_key)
        if not key_data or not key_data["active"]:
            return jsonify({"success": False, "error": "Invalid product key"}), 400
        key_data["assigned_user"] = username
        save_keys(keys)
    users[username] = {
        "password": generate_password_hash(password),
        "is_admin": False,
        "email": email,
        "product_key": product_key
    }
    save_users(users)
    return jsonify({"success": True})

@app.route("/api/verify_key", methods=["POST"])
def verify_key():
    keys = load_keys()
    data = request.json
    product_key = data.get("product_key")
    key_data = keys.get(product_key)
    if not key_data or not key_data["active"]:
        return jsonify({"success": False, "error": "Invalid or inactive key"}), 400
    return jsonify({"success": True, "info": key_data})

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"success": False}), 400
    online = load_online()
    online[username] = {
        "last_seen": time.time(),
        "ip": request.remote_addr
    }
    save_online(online)
    return jsonify({"success": True})

@app.route("/api/check_update", methods=["GET"])
def check_update():
    # Stub: just always return "no update" for now
    return jsonify({"update_available": False, "latest_version": "1.0.0"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
