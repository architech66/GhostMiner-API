import sqlite3
import string
import random
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "super_secret_admin_key"
CORS(app)

DB_PATH = "ghostminer.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                duration TEXT NOT NULL,
                expires_at INTEGER,
                issued_at INTEGER,
                assigned_user_id INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT,
                license_key TEXT,
                created_at INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                message TEXT,
                sent_at INTEGER
            )
        """)
        conn.commit()

init_db()

# Utility functions
def random_license_key(length=16):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def license_time_seconds(duration):
    durations = {
        "24h": 24*3600,
        "1w": 7*24*3600,
        "1m": 30*24*3600,
        "lifetime": 50*365*24*3600
    }
    return durations.get(duration, durations["lifetime"])

@app.route('/admin')
def admin_login_page():
    if session.get("admin"):
        return redirect("/admin/panel")
    return render_template("admin_login.html")

@app.route('/admin/login', methods=["POST"])
def admin_login():
    data = request.json
    if data.get("key") == "YOUR_ADMIN_PANEL_KEY_HERE":  # replace with your real admin key
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid admin key"}), 401

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect("/admin")

@app.route('/admin/panel')
def admin_panel():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin_panel.html")

# ---- LICENSE API ----

@app.route('/api/licenses', methods=["GET"])
def api_get_licenses():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, key, active, duration, expires_at FROM licenses")
        rows = c.fetchall()
        licenses = []
        for row in rows:
            expires_at = row[4]
            time_left = max(0, expires_at - int(time.time())) if expires_at else "Lifetime"
            licenses.append({
                "id": row[0],
                "key": row[1],
                "active": bool(row[2]),
                "duration": row[3],
                "expires_at": expires_at,
                "time_left": time_left
            })
    return jsonify(licenses)

@app.route('/api/licenses', methods=["POST"])
def api_create_license():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    duration = request.json.get("duration", "lifetime")
    key = random_license_key()
    issued_at = int(time.time())
    expires_at = issued_at + license_time_seconds(duration) if duration != "lifetime" else None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO licenses (key, active, duration, expires_at, issued_at) VALUES (?, ?, ?, ?, ?)",
                  (key, 0, duration, expires_at, issued_at))
        conn.commit()
    return jsonify({"key": key, "duration": duration, "expires_at": expires_at})

@app.route('/api/licenses/activate/<license_key>', methods=["POST"])
def api_activate_license(license_key):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE licenses SET active=1 WHERE key=?", (license_key,))
        conn.commit()
    return jsonify({"ok": True})

@app.route('/api/licenses/deactivate/<license_key>', methods=["POST"])
def api_deactivate_license(license_key):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE licenses SET active=0 WHERE key=?", (license_key,))
        conn.commit()
    return jsonify({"ok": True})

@app.route('/api/licenses/delete/<license_key>', methods=["POST"])
def api_delete_license(license_key):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM licenses WHERE key=?", (license_key,))
        conn.commit()
    return jsonify({"ok": True})

@app.route('/api/licenses/update_time/<license_key>', methods=["POST"])
def api_update_license_time(license_key):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    duration = request.json.get("duration", "lifetime")
    expires_at = int(time.time()) + license_time_seconds(duration) if duration != "lifetime" else None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE licenses SET duration=?, expires_at=? WHERE key=?", (duration, expires_at, license_key))
        conn.commit()
    return jsonify({"ok": True})

# ---- USER API ----

@app.route('/api/users', methods=["GET"])
def api_get_users():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, email, license_key FROM users")
        rows = c.fetchall()
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "license_key": row[3]
            })
    return jsonify(users)

@app.route('/api/users', methods=["POST"])
def api_create_user():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")  # You should hash this in production!
    license_key = data.get("license_key")
    created_at = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password, license_key, created_at) VALUES (?, ?, ?, ?, ?)",
                  (username, email, password, license_key, created_at))
        conn.commit()
    # Mark license as assigned/used (optional)
    c = conn.cursor()
    c.execute("UPDATE licenses SET assigned_user_id=(SELECT id FROM users WHERE username=?) WHERE key=?", (username, license_key))
    conn.commit()
    return jsonify({"ok": True})

# ---- FRONTEND ACCOUNT CREATION ----

@app.route('/api/register', methods=["POST"])
def api_register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    license_key = data.get("license_key")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # 1. Check license exists, active, not expired, not used
        c.execute("SELECT id, active, expires_at, assigned_user_id FROM licenses WHERE key=?", (license_key,))
        lic = c.fetchone()
        if not lic:
            return jsonify({"ok": False, "error": "License key not found"}), 404
        if not lic[1]:
            return jsonify({"ok": False, "error": "License not active"}), 403
        if lic[2] and int(time.time()) > lic[2]:
            return jsonify({"ok": False, "error": "License expired"}), 403
        if lic[3]:
            return jsonify({"ok": False, "error": "License already used"}), 403
        # 2. Register user
        c.execute("INSERT INTO users (username, email, password, license_key, created_at) VALUES (?, ?, ?, ?, ?)",
                  (username, email, password, license_key, int(time.time())))
        # 3. Mark license as used
        c.execute("UPDATE licenses SET assigned_user_id=(SELECT id FROM users WHERE username=?) WHERE key=?", (username, license_key))
        conn.commit()
    return jsonify({"ok": True})

@app.route('/api/login', methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username")
    license_key = data.get("license_key")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, license_key FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user and user[1] == license_key:
            return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid credentials"}), 401

# ---- MESSAGES (Admin panel -> users) ----

@app.route('/api/messages', methods=["POST"])
def api_send_message():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    target = data.get("target")  # can be 'all' or comma separated
    message = data.get("message")
    sent_at = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO messages (target, message, sent_at) VALUES (?, ?, ?)", (target, message, sent_at))
        conn.commit()
    # You'd add logic for delivering this message to users (e.g., next API call they make, they receive it)
    return jsonify({"ok": True})

@app.route('/api/messages/inbox/<username>', methods=["GET"])
def api_inbox(username):
    # User fetches their messages (including global/all)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT message FROM messages WHERE target=? OR target='all'", (username,))
        msgs = [row[0] for row in c.fetchall()]
    return jsonify({"messages": msgs})

# ---- Health Check ----
@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
