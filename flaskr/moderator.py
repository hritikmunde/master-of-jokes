from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from flaskr.auth import moderator_required
from flaskr.db import get_db

bp = Blueprint('moderator', __name__, url_prefix='/moderator')

@bp.route('/dashboard')
@moderator_required
def dashboard():
    db = get_db()
    users = db.execute('SELECT id, email, nickname, role, joke_balance FROM user').fetchall()
    return render_template('moderator/dashboard.html', users=users)

@bp.route('/edit_balance/<int:user_id>', methods=['POST'])
@moderator_required
def edit_balance(user_id):
    try:
        new_balance = int(request.form['balance'])
        if new_balance < 0:
            flash('Balance cannot be negative')
            return redirect(url_for('moderator.dashboard'))
            
        db = get_db()
        db.execute(
            'UPDATE user SET joke_balance = ? WHERE id = ?',
            (new_balance, user_id)
        )
        db.commit()
        
        current_app.logger.info(f"User balance updated for user_id {user_id} to {new_balance}")
        flash('Balance updated successfully')
    except ValueError:
        flash('Invalid balance value')
        current_app.logger.warning(f"Invalid balance update attempt for user_id {user_id}")
    
    return redirect(url_for('moderator.dashboard'))

@bp.route('/remove_joke', methods=('POST',))
def remove_joke():
    if not check_role('Moderator'):
        logging.warning('Unauthorized access attempt to remove joke.')
        return redirect(url_for('auth.login'))
    
    joke_id = request.form['joke_id']
    # Logic to remove the joke from the database
    logging.info(f'Moderator {g.user.nickname} removed joke ID: {joke_id}.')
    return redirect(url_for('moderator.dashboard'))

@bp.route('/toggle_role/<int:user_id>', methods=['POST'])
@moderator_required
def toggle_role(user_id):
    db = get_db()
    
    # Check if target user exists
    target_user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    if not target_user:
        flash('User not found')
        return redirect(url_for('moderator.dashboard'))
    
    # Count current moderators
    moderator_count = db.execute(
        'SELECT COUNT(*) as count FROM user WHERE role = ?', 
        ('Moderator',)
    ).fetchone()['count']
    
    new_role = 'User' if target_user['role'] == 'Moderator' else 'Moderator'
    
    # Prevent removal of last moderator
    if new_role == 'User' and moderator_count <= 1:
        flash('Cannot remove the last moderator')
        return redirect(url_for('moderator.dashboard'))
    
    db.execute(
        'UPDATE user SET role = ? WHERE id = ?',
        (new_role, user_id)
    )
    db.commit()
    
    current_app.logger.warning(
        f"User role changed: {target_user['email']} from {target_user['role']} to {new_role}"
    )
    flash(f"Changed {target_user['email']} role to {new_role}")
    return redirect(url_for('moderator.dashboard'))

@bp.route('/jokes')
@moderator_required
def manage_jokes():
    db = get_db()
    jokes = db.execute(
        'SELECT j.*, u.nickname as author_nickname FROM joke j '
        'JOIN user u ON j.author_id = u.id '
        'ORDER BY j.created DESC'
    ).fetchall()
    return render_template('moderator/jokes.html', jokes=jokes)

@bp.route('/joke/<int:joke_id>/edit', methods=['GET', 'POST'])
@moderator_required
def edit_joke(joke_id):
    db = get_db()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        
        if not title or not body:
            flash('Title and body are required.')
        else:
            db.execute(
                'UPDATE joke SET title = ?, body = ? WHERE id = ?',
                (title, body, joke_id)
            )
            db.commit()
            current_app.logger.info(f"Joke {joke_id} edited by moderator {g.user['email']}")
            flash('Joke updated successfully')
            return redirect(url_for('moderator.manage_jokes'))
    
    joke = db.execute('SELECT * FROM joke WHERE id = ?', (joke_id,)).fetchone()
    return render_template('moderator/edit_joke.html', joke=joke)

@bp.route('/joke/<int:joke_id>/delete', methods=['POST'])
@moderator_required
def delete_joke(joke_id):
    db = get_db()
    db.execute('DELETE FROM joke WHERE id = ?', (joke_id,))
    db.commit()
    current_app.logger.warning(f"Joke {joke_id} deleted by moderator {g.user['email']}")
    flash('Joke deleted successfully')
    return redirect(url_for('moderator.manage_jokes'))
