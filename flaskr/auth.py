import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db
from .logging_utils import log_auth_success, log_auth_failure, log_role_change

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        nickname = request.form['nickname']
        password = request.form['password']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
            current_app.logger.warning("User registration failed: Missing email.")
        elif not nickname:
            error = 'Nickname is required.'
            current_app.logger.warning("User registration failed: Missing nickname.")
        elif not password:
            error = 'Password is required.'
            current_app.logger.warning("User registration failed: Missing password.")

        elif db.execute(
            'SELECT id FROM user WHERE email = ? OR nickname = ?', (email, nickname)
        ).fetchone() is not None:
            error = 'Email or Nickname already exists.'

        if error is None:
            db.execute(
                'INSERT INTO user (email, nickname, password, joke_balance) VALUES (?, ?, ?, 0)',
                (email, nickname, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email_or_nickname = request.form['email_or_nickname']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE email = ? OR nickname = ?', (email_or_nickname, email_or_nickname)
        ).fetchone()

        if user is None:
            error = 'Incorrect email or nickname.'
            log_auth_failure(email_or_nickname, "User not found")
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
            log_auth_failure(user['email'], "Invalid password")

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            log_auth_success(user)
            current_app.logger.info(f"User logged in: {user['email']}")
            return redirect(url_for('jokes.my_jokes'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT id, email, nickname, password, joke_balance, role FROM user WHERE id = ?',
            (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.register'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def moderator_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        if g.user['role'] != 'Moderator':
            current_app.logger.warning(f"Unauthorized moderator access attempt by user {g.user['email']}")
            flash('You must be a moderator to access this page.')
            return redirect(url_for('index'))
            
        return view(**kwargs)
    return wrapped_view