import os, json, time
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-key")

USER_FILE = "users.json"
ONLINE_FILE = "online.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def load_online():
    if not os.path.exists(ONLINE_FILE):
        return {}
    with open(ONLINE_FILE, "r") as f:
        return json.load(f)

def save_online(online):
    with open(ONLINE_FILE, "w") as f:
        json.dump(online, f)

@app.route("/")
def root():
    return redirect(url_for("admin_login"))

# -------------------- ADMIN PANEL ---------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        if username in users and check_password_hash(users[username]["password"], password) and users[username].get("is_admin"):
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

def require_admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    users = load_users()
    online = load_online()
    return render_template("dashboard.html", users=users, online=online)

@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    users = load_users()
    username = request.form.get("username")
    password = request.form.get("password")
    is_admin = request.form.get("is_admin") == "on"
    if username in users:
        return redirect(url_for("admin_dashboard") + "?error=User+already+exists")
    users[username] = {
        "password": generate_password_hash(password),
        "is_admin": is_admin
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

# ------------------- API ROUTES ---------------------

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})

@app.route("/api/login", methods=["POST"])
def login():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username in users and check_password_hash(users[username]["password"], password):
        # Record "online"
        online = load_online()
        online[username] = {
            "last_seen": time.time(),
            "ip": request.remote_addr
        }
        save_online(online)
        return jsonify({"success": True, "token": "FAKE_TOKEN"})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
