from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json

app = Flask(__name__)
app.secret_key = "your-very-secret-key"  # CHANGE this for security

# Hard-coded admin key for now
ADMIN_KEY = "HTvXHtzE5u3F7BQ8zjLA4KvW"  # replace if you want

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"users": [], "logs": []}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_authenticated():
    return session.get("authenticated", False)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    # Already logged in? Go to panel
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
    # Loads data, passes to panel template
    data = load_data()
    return render_template("admin_panel.html", data=data)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# Example API endpoint for your fake miner/app to send logs/users to the backend
@app.route("/api/track", methods=["POST"])
def track():
    content = request.json
    data = load_data()
    if "user" in content:
        data["users"].append(content["user"])
    if "log" in content:
        data["logs"].append(content["log"])
    save_data(data)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
