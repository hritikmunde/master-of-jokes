from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, abort, current_app
)
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('jokes', __name__, url_prefix='/jokes')

def get_joke(id):
    db = get_db()
    joke = db.execute(
        'SELECT j.id, title, body, created, author_id, nickname'
        ' FROM joke j JOIN user u ON j.author_id = u.id'
        ' WHERE j.id = ?',
        (id,)
    ).fetchone()

    if joke is None:
        abort(404, f"Joke id {id} doesn't exist.")

    if joke['author_id'] != g.user['id']:
        abort(403)

    return joke

@bp.route('/leave', methods=('GET', 'POST'))
@login_required
def leave_joke():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        db = get_db()
        error = None

        if not title:
            error = 'Title is required.'
            current_app.logger.warning("Joke submission failed: Missing title.")
        elif len(title.split()) > 10:
            error = 'Title must be 10 words or fewer.'
        elif db.execute(
            'SELECT id FROM joke WHERE title = ? AND author_id = ?', (title, g.user['id'])
        ).fetchone() is not None:
            error = 'You have already used this title for a joke.'

        if error is None:
            db.execute(
                'INSERT INTO joke (title, body, author_id) VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.execute(
                'UPDATE user SET joke_balance = joke_balance + 1 WHERE id = ?',
                (g.user['id'],)
            )
            db.commit()
            current_app.logger.info(f"Joke created: '{title}' by {g.user['nickname']}")
            return redirect(url_for('jokes.my_jokes'))

        flash(error)

    return render_template('jokes/leave.html')

@bp.route('/<int:id>/rate', methods=['POST'])
@login_required
def rate_joke(id):
    rating = int(request.form['rating'])
    db = get_db()
    
    # Update the rating in joke_taken
    db.execute(
        'UPDATE joke_taken SET rating = ? WHERE joke_id = ? AND user_id = ?',
        (rating, id, g.user['id'])
    )
    
    # Calculate and update average rating in joke table
    avg_rating = db.execute(
        'SELECT AVG(rating) as avg_rating FROM joke_taken WHERE joke_id = ? AND rating IS NOT NULL',
        (id,)
    ).fetchone()['avg_rating']
    
    if avg_rating is not None:
        db.execute(
            'UPDATE joke SET rating = ? WHERE id = ?',
            (avg_rating, id)
        )
    
    db.commit()
    return redirect(request.referrer)

@bp.route('/my_jokes')
@login_required
def my_jokes():
    db = get_db()
    jokes = db.execute(
        'SELECT id, title, body, rating, created FROM joke WHERE author_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    return render_template('jokes/my_jokes.html', jokes=jokes)

@bp.route('/take')
@login_required
def take_joke():
    db = get_db()
    # Get all jokes not authored by current user
    jokes = db.execute(
        'SELECT j.id, j.title, j.body, j.rating, j.created, '
        '(SELECT nickname FROM user WHERE id = j.author_id) as author_nickname, '
        '(SELECT rating FROM joke_taken WHERE joke_id = j.id AND user_id = ?) as user_rating, '
        'EXISTS(SELECT 1 FROM joke_taken WHERE joke_id = j.id AND user_id = ?) as is_taken '
        'FROM joke j '
        'WHERE j.author_id != ? '
        'ORDER BY j.created DESC',
        (g.user['id'], g.user['id'], g.user['id'])
    ).fetchall()
    
    # Get list of jokes already taken by user
    taken_jokes = db.execute(
        'SELECT joke_id FROM joke_taken WHERE user_id = ?',
        (g.user['id'],)
    ).fetchall()
    taken_jokes = [joke['joke_id'] for joke in taken_jokes]
    
    return render_template('jokes/take.html', jokes=jokes, taken_jokes=taken_jokes)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_joke(id)
    db = get_db()
    db.execute('DELETE FROM joke WHERE id = ?', (id,))
    db.execute(
        'UPDATE user SET joke_balance = joke_balance - 1 WHERE id = ?',
        (g.user['id'],)
    )
    db.commit()
    return redirect(url_for('jokes.my_jokes'))

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    joke = get_joke(id)

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Body is required.'

        if error is None:
            db = get_db()
            db.execute(
                'UPDATE joke SET body = ? WHERE id = ? AND author_id = ?',
                (body, id, g.user['id'])
            )
            db.commit()
            return redirect(url_for('jokes.view_joke', id = id))

        flash(error)

    return render_template('jokes/edit.html', joke=joke)

@bp.route('/<int:id>/take', methods=['POST'])
@login_required
def take_single(id):
    db = get_db()
    
    # Check if user has enough joke balance
    if g.user['joke_balance'] <= 0:
        flash('Your joke balance is too low!')
        return redirect(url_for('jokes.take_joke'))
    
    # Check if user has already taken this joke
    if db.execute(
        'SELECT 1 FROM joke_taken WHERE user_id = ? AND joke_id = ?',
        (g.user['id'], id)
    ).fetchone() is not None:
        flash('You have already taken this joke!')
        return redirect(url_for('jokes.take_joke'))
    
    # Check if joke exists and user isn't the author
    joke = db.execute(
        'SELECT author_id FROM joke WHERE id = ?',
        (id,)
    ).fetchone()
    
    if joke is None:
        abort(404)
    if joke['author_id'] == g.user['id']:
        abort(403)
    
    # Take the joke
    db.execute(
        'INSERT INTO joke_taken (user_id, joke_id) VALUES (?, ?)',
        (g.user['id'], id)
    )
    
    # Decrease user's joke balance
    db.execute(
        'UPDATE user SET joke_balance = joke_balance - 1 WHERE id = ?',
        (g.user['id'],)
    )
    
    db.commit()
    flash('Joke taken successfully!')
    return redirect(url_for('jokes.view_joke', id = id))

@bp.route('/<int:id>', methods=('GET',))
@login_required
def view_joke(id):
    db = get_db()
    is_taken = bool(db.execute("select exists(select * from joke_taken where user_id = ? and joke_id = ?) as is_taken", (g.user["id"], id)).fetchone()["is_taken"])

    joke = db.execute(
       "select *, (SELECT rating FROM joke_taken WHERE joke_id = j.id AND user_id = ?) as user_rating from joke j inner join user u on (u.id = j.author_id) where j.id = ?",
        (g.user["id"], id),
    ).fetchone()

    if not is_taken and g.user["id"] != joke["author_id"]:
        flash("you have not taken this joke")
        return redirect(url_for("index"))
    return render_template('jokes/view.html', joke=joke)
