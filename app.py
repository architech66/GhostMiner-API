from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = "something-super-secret"  # make sure you’ve got one

# simple login_required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# 1) LOGIN
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        # your real auth check here
        if u == "architect66" and p == "yourpassword":
            session["logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        # else just fall through and re-render
    return render_template("login.html")


# 2) DASHBOARD
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    return render_template("dashboard.html")


# 3) WALLET CRACKER
@app.route("/admin/wallet_cracker")
@login_required
def wallet_cracker():
    # stub – you’ll fill this in
    return "wallet cracker page"


# 4) BALANCE CHECKER
@app.route("/admin/balance_checker")
@login_required
def balance_checker():
    # stub
    return "balance checker page"


# 5) LOGS
@app.route("/admin/logs")
@login_required
def logs():
    # stub
    return render_template("logs.html", logs=[])


# 6) SETTINGS
@app.route("/admin/settings", methods=["GET","POST"])
@login_required
def settings():
    # stub
    return "settings page"


# 7) LOGOUT
@app.route("/admin/logout")
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(debug=True)
