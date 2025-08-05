from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# --- Config ---
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- Home redirect to admin login ---
@app.route('/')
def home():
    return redirect(url_for('admin_login'))

# --- Admin Login page ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        for user in users:
            if user['username'] == username and user['password'] == password:
                return render_template('dashboard.html', username=username)
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

# --- API: Login for the app ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    users = load_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# --- API: Status check ---
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({"status": "online", "version": "1.0.0"})

# --- 404 page for all others ---
@app.errorhandler(404)
def not_found(e):
    return "Not Found", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
