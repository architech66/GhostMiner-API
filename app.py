from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'changeme')

USERS_FILE = 'users.json'
NOTIF_FILE = 'notifications.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_notifications():
    if not os.path.exists(NOTIF_FILE):
        return []
    with open(NOTIF_FILE, 'r') as f:
        return json.load(f)

def save_notifications(notifs):
    with open(NOTIF_FILE, 'w') as f:
        json.dump(notifs, f, indent=2)

# --- API: Login ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    users = load_users()
    if username not in users:
        return jsonify({"success": False, "error": "Invalid username or password"})
    if not check_password_hash(users[username]["password"], password):
        return jsonify({"success": False, "error": "Invalid username or password"})
    # Session token would be here if you want it
    return jsonify({"success": True, "is_admin": users[username].get("is_admin", False)})

# --- API: Register/Create Account ---
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    product_key = data.get("product_key", "")
    users = load_users()
    if username in users:
        return jsonify({"success": False, "error": "Username already exists"})
    hashed = generate_password_hash(password)
    users[username] = {
        "password": hashed,
        "email": email,
        "product_key": product_key,
        "is_admin": False
    }
    save_users(users)
    return jsonify({"success": True})

# --- API: Check for Updates (Dummy Example) ---
@app.route('/api/check_update', methods=['GET'])
def api_check_update():
    # Implement your own versioning if you want
    return jsonify({"update_available": False})

# --- API: Ping ---
@app.route('/api/ping', methods=['GET'])
def api_ping():
    return jsonify({"pong": True})

# --- API: Notifications ---
@app.route('/api/notifications', methods=['POST'])
def send_notification():
    data = request.json
    message = data.get('message')
    users = data.get('users', [])  # Empty = all users
    notif = {
        "message": message,
        "users": users,
        "timestamp": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4()),
        "read_by": []
    }
    notifs = load_notifications()
    notifs.append(notif)
    save_notifications(notifs)
    return jsonify({"success": True})

@app.route('/api/fetch_notifications', methods=['POST'])
def fetch_notifications():
    data = request.json
    username = data.get('username')
    notifs = load_notifications()
    result = []
    for n in notifs:
        if (not n['users'] or username in n['users']) and username not in n.get("read_by", []):
            result.append({"id": n["id"], "message": n["message"]})
    return jsonify({"notifications": result})

@app.route('/api/mark_notification', methods=['POST'])
def mark_notification():
    data = request.json
    notif_id = data.get('id')
    username = data.get('username')
    notifs = load_notifications()
    for n in notifs:
        if n['id'] == notif_id:
            if "read_by" not in n:
                n["read_by"] = []
            if username not in n["read_by"]:
                n["read_by"].append(username)
            break
    save_notifications(notifs)
    return jsonify({"success": True})

# --- Admin: Web Page (Login and Send Notifications) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username].get("is_admin") and check_password_hash(users[username]["password"], password):
            session['admin'] = username
            return redirect(url_for('admin_panel'))
        msg = 'Invalid login'
    return render_template('login.html', msg=msg)

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    users = load_users()
    msg = ''
    if request.method == 'POST':
        # Send notification from web
        message = request.form['message']
        recipients = request.form.getlist('users')
        if 'all' in recipients:
            reci
