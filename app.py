# app.py
import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from functools import wraps

app = Flask(
    __name__,
    static_folder="static",      # serve /static/..
    template_folder="templates"  # render from /templates/..
)

# Secret key (in prod, set via Render's env vars)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


# Simple login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in first.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------

@app.route("/")
def home():
    # Redirect root → login
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # --- YOUR AUTH CHECK HERE ---
        # Replace with real user lookup
        if username == "architect66" and password == "yourpassword":
            session["logged_in"] = True
            session["user"] = username
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    # No data needed here—just show the UI & snow
    return render_template("dashboard.html")


@app.route("/admin/wallet_cracker")
@login_required
def wallet_cracker():
    # Stub: later you’ll launch the CLI sim
    return "<h1>🔓 Wallet Cracker module coming soon...</h1>"


@app.route("/admin/balance_checker", methods=["GET", "POST"])
@login_required
def balance_checker():
    # Stub: you can integrate live & fake modes here
    if request.method == "POST":
        # handle lookup form
        pass
    return render_template("balance_checker.html")


@app.route("/admin/logs")
@login_required
def logs():
    # Pull from your log store; stub with empty list
    fake_logs = []
    return render_template("logs.html", logs=fake_logs)


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def settings():
    # Stub: let user change their “cashout” wallet address here
    if request.method == "POST":
        # save settings
        pass
    return render_template("settings.html")


# ------------------------------------------------------------
# ERROR HANDLERS
# ------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("admin_login"))  # send everything back to login


@app.errorhandler(500)
def server_error(e):
    # log the error, then show a friendly page
    app.logger.error(f"Server Error: {e}")
    return (
        render_template("500.html", error=str(e)),
        500
    )


# ------------------------------------------------------------
# LAUNCH
# ------------------------------------------------------------
if __name__ == "__main__":
    # Detect Render's $PORT (or default to 5000 locally)
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 so Render can see it
    app.run(host="0.0.0.0", port=port, debug=True)
