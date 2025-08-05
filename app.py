from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'CHANGE_THIS_SECRET_KEY'
DATABASE = 'ghostminer.db'

# CHANGE THIS: This is your admin login key (24 chars, example)
ADMIN_KEY = 'B28tV1q6TbShZ9e5rQa6uP3w'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.before_request
def initialize_db_once():
    if not hasattr(app, 'db_initialized'):
        if not os.path.exists(DATABASE):
            db = sqlite3.connect(DATABASE)
            c = db.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    email TEXT,
                    password TEXT,
                    key TEXT
                )
            ''')
            db.commit()
            db.close()
        app.db_initialized = True

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return redirect(url_for('admin_login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        key = request.form.get('admin_key')
        if key == ADMIN_KEY:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid key')
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    # Show a super basic panel for now
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, username, email, key FROM users')
    users = c.fetchall()
    return render_template('admin_panel.html', users=users)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
