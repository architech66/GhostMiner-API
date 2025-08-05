import os
import sqlite3
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "replace-this-with-something-secret"

DB_PATH = "ghostminer.db"
ADMIN_KEY = "B28tV1q6TbShZ9e5rQa6uP3w"  # Replace with your key!

# --------- SQLite DB INIT ----------
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
            key TEXT NOT NULL UNIQUE
        )''')
        conn.commit()
init_db()

# --------- ADMIN PANEL ROUTES ----------
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
    return render_template('admin_panel.html', users=users)

# --------- ADMIN PANEL AJAX API ----------
@app.route('/api/generate_license', methods=['POST'])
def generate_license():
    if not session.get('admin'):
        return jsonify({'success': False, 'msg': 'Unauthorized'})
    # Generate unique 16 digit key
    new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute('INSERT INTO licenses (key) VALUES (?)', (new_key,))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'msg': 'Duplicate key'})
    return jsonify({'success': True, 'license': new_key})

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

@app.route('/api/get_messages', methods=['POST'])
def get_messages():
    data = request.get_json()
    username = data.get('username')
    with sqlite3.connect(DB_PATH) as conn:
        msgs = conn.execute('SELECT message FROM messages WHERE target=? OR target="all"', (username,)).fetchall()
    return jsonify([m[0] for m in msgs])

# --------- API FOR TOOL FRONTEND ---------
@app.route('/api/create_account', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    license_key = data.get('license_key')

    # Check if license exists and is unused
    with sqlite3.connect(DB_PATH) as conn:
        lic = conn.execute('SELECT * FROM licenses WHERE key=?', (license_key,)).fetchone()
        if not lic:
            return jsonify({'success': False, 'msg': 'Invalid license'})
        # Remove license after use
        conn.execute('DELETE FROM licenses WHERE key=?', (license_key,))
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
    if user:
        return jsonify({'success': True, 'user': {'id': user[0], 'username': user[1], 'email': user[2]}})
    else:
        return jsonify({'success': False, 'msg': 'Invalid login'})

# --------- MAIN ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
