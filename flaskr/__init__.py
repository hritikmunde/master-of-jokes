import os
import logging
from . import db, auth, jokes, moderator, logging_routes  
from logging.handlers import RotatingFileHandler
from flask import Flask, g, redirect, url_for, render_template
import click
from werkzeug.security import generate_password_hash
from .db import get_db

def setup_logging(app):
    # Log directory setup
    log_dir = os.path.join(app.instance_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Logging file handler (rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'master_of_jokes.log'),
        maxBytes=10000,
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z'
    )
    file_handler.setFormatter(formatter)

    # Add handler to Flask app
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    app.logger.addHandler(console_handler)
    app.logger.info("Logging setup complete.")

    @app.route('/logging/level/<level>', methods=['POST'])
    def set_log_level(level):
        if not g.user or g.user.get('role') != 'Moderator':
            return "Unauthorized", 403
            
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level in levels:
            app.logger.setLevel(levels[level])
            app.logger.info(f"Log level changed to {level}")
            return f"Log level set to {level}", 200
        return "Invalid log level", 400

def create_app():
    # Create/Configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # Ensure instance folder exists
    try: os.makedirs(app.instance_path)
    except OSError: pass

    # Initialize logging
    setup_logging(app)

    # Register blueprints

    @app.route('/')
    # def index(): return 'Welcome to Master of Jokes!'
    def index():
        if not g.user:
            return redirect(url_for('auth.login'))  # Redirect if not logged in
        return render_template('base.html')  # Load the main content if logged in

    db.init_app(app)
    app.add_url_rule("/", endpoint="index")

    
    app.register_blueprint(auth.bp)
    app.register_blueprint(jokes.bp)
    app.register_blueprint(moderator.bp)
    app.register_blueprint(logging_routes.bp)

    @app.before_request
    def before_request():
        from .logging_utils import log_request
        log_request()

    @app.after_request
    def after_request(response):
        from .logging_utils import log_response
        return log_response(response)
        
    app.logger.info("Application starting up")
    
    @app.cli.command('init-moderator')
    @click.argument('username')
    @click.argument('email')
    def init_moderator_command(username, email):
        """Initialize a moderator user."""
        db = get_db()
        
        user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
        if user:
            db.execute('UPDATE user SET role = ? WHERE email = ?', ('Moderator', email))
            click.echo(f'Updated user {username} ({email}) to Moderator role.')
        else:
            password = input("Enter Password for Moderator: ")
            db.execute(
                'INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)',
                (email, username, generate_password_hash(password), 'Moderator')
            )
            click.echo(f'Created new moderator user: {username} ({email})')
        
        db.commit()

    return app
