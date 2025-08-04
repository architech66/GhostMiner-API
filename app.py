# app.py

import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from extensions import db, login_manager, cors
from models import User, LoginLog
from config import Config

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    cors.init_app(app)

    # ——— Database & Default Admin Setup ——————————————————————
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='architect66').first():
            admin = User(username='architect66')
            admin.set_password('337333')
            db.session.add(admin)
            db.session.commit()

    # ——— Routes ———————————————————————————————————————————
    @app.route('/admin/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username']).first()
            ip   = request.remote_addr
            ok   = False
            if user and user.check_password(request.form['password']):
                login_user(user)
                flash('Login successful','success')
                ok = True
                return redirect(url_for('dashboard'))
            flash('Invalid credentials','danger')
            db.session.add(LoginLog(
                username=request.form.get('username'),
                ip_address=ip,
                successful=ok
            ))
            db.session.commit()
        return render_template('login.html')

    @app.route('/admin/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/admin/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/admin/users')
    @login_required
    def users():
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('users.html', users=users)

    @app.route('/admin/users/new', methods=['GET','POST'])
    @login_required
    def new_user():
        if request.method == 'POST':
            u = User(username=request.form['username'])
            u.set_password(request.form['password'])
            db.session.add(u)
            db.session.commit()
            return redirect(url_for('users'))
        return render_template('user_form.html')

    @app.route('/admin/logs')
    @login_required
    def logs():
        logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).all()
        return render_template('logs.html', logs=logs)

    return app

if __name__=="__main__":
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
