from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123")
AUTH_KEY = os.environ.get("ADMIN_AUTH_KEY", "R2d7FA3TxvJ9wP6Zq1MbKvB8")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        entered_key = request.form.get('auth_key')
        if entered_key == AUTH_KEY:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_key_login.html', error='Invalid Auth Key.')
    return render_template('admin_key_login.html', error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/')
def index():
    return "GhostMiner API is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
