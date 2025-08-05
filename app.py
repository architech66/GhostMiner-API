from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# SECRET KEY for sessions (change for prod)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123")

# --- ADMIN LOGIN PAGE ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple hardcoded login, update as needed
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials.')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# --- API EXAMPLE ---
@app.route('/api/notifications', methods=['POST'])
def api_notifications():
    data = request.json
    # Here you would process the data...
    return jsonify({"status": "success", "data": data}), 200

# --- MAIN ROUTE FOR FRONTEND ---
@app.route('/')
def index():
    return render_template('index.html')  # Replace with your frontend or landing page

# --- ERROR HANDLERS (for better debugging) ---
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html", error=e), 500

if __name__ == '__main__':
    # Render uses its own webserver; locally you can test on any port
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
