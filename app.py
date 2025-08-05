import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
import os

app = Flask(__name__)
app.secret_key = "your-very-secret-key"

ADMIN_KEY = "HTvXHtzE5u3F7BQ8zjLA4KvW"  # Replace this with your real key

DATABASE = "ghostminer.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        db.commit()

@app.before_first_request
def setup():
    init_db()

def is_authenticated():
    return session.get("authenticated", False)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if is_authenticated():
        return redirect(url_for("admin_panel"))
    error = None
    if request.method == "POST":
        auth_key = request.form.get("auth_key", "")
        if auth_key == ADMIN_KEY:
            session["authenticated"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Invalid key."
    return render_template("admin_login.html", error=error)

@app.route("/admin/panel")
def admin_panel():
    if not is_authenticated():
        return redirect(url_for("admin_login"))
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    logs = db.execute("SELECT * FROM logs ORDER BY created_at DESC").fetchall()
    return render_template("admin_panel.html", users=users, logs=logs)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/api/track", methods=["POST"])
def track():
    content = request.json
    db = get_db()
    if "user" in content:
        db.execute("INSERT INTO users (username) VALUES (?)", (content["user"],))
    if "log" in content:
        db.execute("INSERT INTO logs (message) VALUES (?)", (content["log"],))
    db.commit()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
