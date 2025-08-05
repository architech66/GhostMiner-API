import os
import sqlite3
import random
import string
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "replace-this-with-something-secret"

DB_PATH = "ghostminer.db"
ADMIN_KEY = "B28tV1q6TbShZ9e5rQa6uP3w"  # Your admin login key

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            key TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            message TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            active INTEGER DEFAULT 0,
            expires_at TEXT,
            duration TEXT DEFAULT 'lifetime'
        )''')
        conn.commit()
init_db()

def expiry_from_duration(duration):
    now = datetime.datetime.utcnow()
    if duration == '24h':
        return (now + datetime.timedelta(hours=24)).isoformat()
    elif duration == '1w':
        return (now + datetime.timedelta(weeks=1)).isoformat()
    elif duration == '1m':
        return (now + datetime.timedelta(days=30)).isoformat()
    elif duration == 'lifetime':
        return None
    return None

# --- ADMIN LOGIN ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    error = None
    if request.method == 'POST':
        key = request.form.get('admin_key')
        if key == ADMIN_KEY:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Invalid key"
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    with sqlite3.connect(DB_PATH) as conn:
        users = conn.execute('SELECT * FROM users').fetchall()
        licenses = conn.execute('SELECT * FROM licenses').fetchall()
    return render_template('admin_panel.html', users=users, licenses=licenses)

# --- LICENSE API ---
@app.route('/api/generate_license', methods=['POST'])
def generate_license():
    if not session.get('admin'):
        return jsonify({'success': False, 'msg': 'Unauthorized'})
    # Generate unique 16 digit key
    new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute('INSERT INTO licenses (key, active, duration) VALUES (?, 0, ?)', (new_key, 'lifetime'))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'msg': 'Duplicate key'})
    return jsonify({'success': True, 'license': new_key})

@app.route('/api/licenses', methods=['GET'])
def get_licenses():
    if not session.get('admin'):
        return jsonify([])
    with sqlite3.connect(DB_PATH) as conn:
        licenses = conn.execute('SELECT * FROM licenses').fetchall()
    def format_expiry(exp):
        if not exp:
            return "∞"
        dt = datetime.datetime.fromisoformat(exp)
        remaining = dt - datetime.datetime.utcnow()
        if remaining.total_seconds() < 0:
            return "Expired"
        days, seconds = divmod(remaining.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        return f"{int(days)}d {int(hours)}h"
    result = []
    for lic in licenses:
        result.append({
            "id": lic[0],
            "key": lic[1],
            "active": bool(lic[2]),
            "expires_at": lic[3],
            "duration": lic[4],
            "time_left": format_expiry(lic[3])
        })
    return jsonify(result)

@app.route('/api/set_license_active', methods=['POST'])
def set_license_active():
    if not session.get('admin'):
        return jsonify({'success': False})
    data = request.get_json()
    license_id = data.get('license_id')
    active = data.get('active')
    duration = data.get('duration')
    expires_at = expiry_from_duration(duration) if active else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE licenses SET active=?, duration=?, expires_at=? WHERE id=?',
            (1 if active else 0, duration, expires_at, license_id))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/delete_license', methods=['POST'])
def delete_license():
    if not session.get('admin'):
        return jsonify({'success': False})
    data = request.get_json()
    license_id = data.get('license_id')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM licenses WHERE id=?', (license_id,))
        conn.commit()
    return jsonify({'success': True})

# --- USERS, MESSAGES, ETC ---
@app.route('/api/get_users', methods=['GET'])
def get_users():
    if not session.get('admin'):
        return jsonify([])
    with sqlite3.connect(DB_PATH) as conn:
        users = conn.execute('SELECT * FROM users').fetchall()
    return jsonify([
        {'id': u[0], 'username': u[1], 'email': u[2], 'key': u[3]}
        for u in users
    ])

@app.route('/api/send_message', methods=['POST'])
def send_message():
    if not session.get('admin'):
        return jsonify({'success': False, 'msg': 'Unauthorized'})
    data = request.get_json()
    message = data.get('message')
    targets = data.get('targets', [])
    with sqlite3.connect(DB_PATH) as conn:
        for target in targets:
            conn.execute('INSERT INTO messages (target, message) VALUES (?,?)', (target, message))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/get_messages', methods=['POST'])
def get_messages():
    data = request.get_json()
    username = data.get('username')
    with sqlite3.connect(DB_PATH) as conn:
        msgs = conn.execute('SELECT message FROM messages WHERE target=? OR target="all"', (username,)).fetchall()
    return jsonify([m[0] for m in msgs])

# --- TOOL FRONTEND LOGIN/API ---
@app.route('/api/create_account', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    license_key = data.get('license_key')

    with sqlite3.connect(DB_PATH) as conn:
        # Only accept active, non-expired licenses
        lic = conn.execute('SELECT * FROM licenses WHERE key=? AND active=1', (license_key,)).fetchone()
        if not lic:
            return jsonify({'success': False, 'msg': 'Invalid or inactive license'})
        # Check expiry
        if lic[3]:
            if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(lic[3]):
                return jsonify({'success': False, 'msg': 'License expired'})
        # Mark as used (delete? or keep for tracking—here we keep, just let login use again while active/valid)
        # Add user:
        conn.execute('INSERT INTO users (username, email, key) VALUES (?, ?, ?)', (username, email, license_key))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    license_key = data.get('license_key')
    with sqlite3.connect(DB_PATH) as conn:
        user = conn.execute('SELECT * FROM users WHERE username=? AND key=?', (username, license_key)).fetchone()
        # Only allow login if license is still active/valid
        lic = conn.execute('SELECT * FROM licenses WHERE key=? AND active=1', (license_key,)).fetchone()
        if not user or not lic:
            return jsonify({'success': False, 'msg': 'Invalid login or license inactive'})
        if lic[3]:  # has expiry
            if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(lic[3]):
                return jsonify({'success': False, 'msg': 'License expired'})
    return jsonify({'success': True, 'user': {'id': user[0], 'username': user[1], 'email': user[2]}})

# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
