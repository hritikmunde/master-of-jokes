from flask import Blueprint, flash, redirect, url_for, current_app
from flaskr.auth import moderator_required

bp = Blueprint('logging', __name__, url_prefix='/logging')

@bp.route('/level/<level>')
@moderator_required
def set_level(level):
    if level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        current_app.logger.setLevel(level.upper())
        flash(f'Logging level set to {level.upper()}')
    else:
        flash('Invalid logging level')
    return redirect(url_for('moderator.dashboard')) 