import os
import uuid
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'beerfest-secret-key-change-me')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_DIM = 900
IMAGE_QUALITY = 82

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB

CATEGORIES = [
    ('best_ipa',      'Best IPA',               '🍺'),
    ('best_dark',     'Best Dark Beer',          '🖤'),
    ('best_sour',     'Best Sour / Fruit Beer',  '🍋'),
    ('best_lager',    'Best Lager / Pilsner',    '🌾'),
    ('best_non_beer', 'Best Non-Beer',           '🍹'),
    ('most_unique',   'Most Unique',             '✨'),
    ('best_label',    'Best Label',              '🎨'),
    ('best_overall',  'Best Overall',            '🏆'),
    ('worst_overall', 'Worst Overall',           '💀'),
]

VOTES_PER_CATEGORY = 3
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'beerfest')


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect('beerfest.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS beers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            guest_name  TEXT NOT NULL,
            image_path  TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS votes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            beer_id     INTEGER NOT NULL,
            category    TEXT NOT NULL,
            voter_id    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(beer_id, category, voter_id),
            FOREIGN KEY (beer_id) REFERENCES beers(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        INSERT OR IGNORE INTO settings (key, value) VALUES ('results_revealed', 'false');
    ''')
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_obj, original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    save_ext = 'jpg' if ext in ('jpg', 'jpeg') else ext
    filename = f"{uuid.uuid4()}.{save_ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    img = Image.open(file_obj)
    img = img.convert('RGB') if img.mode in ('RGBA', 'P') else img
    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)
    img.save(path, quality=IMAGE_QUALITY, optimize=True)

    return 'uploads/' + filename


def results_revealed():
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='results_revealed'").fetchone()
    conn.close()
    return row and row['value'] == 'true'


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in as admin first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Before-request: ensure each browser has a persistent voter ID
# ---------------------------------------------------------------------------

@app.before_request
def ensure_voter_id():
    if 'voter_id' not in session:
        session['voter_id'] = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Routes – public
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    conn = get_db()
    beer_count = conn.execute('SELECT COUNT(*) FROM beers').fetchone()[0]
    vote_count = conn.execute('SELECT COUNT(*) FROM votes').fetchone()[0]
    conn.close()
    return render_template('index.html',
                           beer_count=beer_count,
                           vote_count=vote_count,
                           categories=CATEGORIES)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        guest_name = request.form.get('guest_name', '').strip()

        if not name or not guest_name:
            flash('Both beer name and your name are required.', 'error')
            return redirect(url_for('register'))

        image_path = None
        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            try:
                image_path = save_image(file, file.filename)
            except Exception:
                flash('Image could not be processed – beer registered without photo.', 'warning')

        conn = get_db()
        conn.execute(
            'INSERT INTO beers (name, guest_name, image_path) VALUES (?, ?, ?)',
            (name, guest_name, image_path)
        )
        conn.commit()
        conn.close()

        flash(f'"{name}" has been added to the festival! Cheers! 🍺', 'success')
        return redirect(url_for('beers'))

    return render_template('register.html')


@app.route('/beers')
def beers():
    conn = get_db()
    all_beers = conn.execute('SELECT * FROM beers ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('beers.html', beers=all_beers)


@app.route('/vote')
def vote_home():
    voter_id = session['voter_id']
    conn = get_db()
    vote_counts = {}
    for cat_id, _, _ in CATEGORIES:
        n = conn.execute(
            'SELECT COUNT(*) FROM votes WHERE category=? AND voter_id=?',
            (cat_id, voter_id)
        ).fetchone()[0]
        vote_counts[cat_id] = n
    conn.close()
    return render_template('vote_home.html', categories=CATEGORIES,
                           vote_counts=vote_counts,
                           votes_per_category=VOTES_PER_CATEGORY)


@app.route('/vote/<category_id>')
def vote(category_id):
    cat = next((c for c in CATEGORIES if c[0] == category_id), None)
    if not cat:
        return redirect(url_for('vote_home'))

    voter_id = session['voter_id']
    conn = get_db()
    all_beers = conn.execute('SELECT * FROM beers ORDER BY name').fetchall()
    voted_ids = {
        row['beer_id'] for row in conn.execute(
            'SELECT beer_id FROM votes WHERE category=? AND voter_id=?',
            (category_id, voter_id)
        ).fetchall()
    }
    conn.close()

    votes_used = len(voted_ids)
    return render_template('vote.html',
                           category=cat,
                           beers=all_beers,
                           voted_ids=voted_ids,
                           votes_used=votes_used,
                           votes_per_category=VOTES_PER_CATEGORY,
                           categories=CATEGORIES)


@app.route('/vote/<category_id>/toggle', methods=['POST'])
def toggle_vote(category_id):
    cat = next((c for c in CATEGORIES if c[0] == category_id), None)
    if not cat:
        return jsonify(error='Invalid category'), 400

    voter_id = session['voter_id']
    data = request.get_json(silent=True) or {}
    beer_id = data.get('beer_id')

    if not beer_id:
        return jsonify(error='Missing beer_id'), 400

    conn = get_db()

    existing = conn.execute(
        'SELECT id FROM votes WHERE beer_id=? AND category=? AND voter_id=?',
        (beer_id, category_id, voter_id)
    ).fetchone()

    if existing:
        conn.execute(
            'DELETE FROM votes WHERE beer_id=? AND category=? AND voter_id=?',
            (beer_id, category_id, voter_id)
        )
        conn.commit()
        voted = False
    else:
        current = conn.execute(
            'SELECT COUNT(*) FROM votes WHERE category=? AND voter_id=?',
            (category_id, voter_id)
        ).fetchone()[0]
        if current >= VOTES_PER_CATEGORY:
            conn.close()
            return jsonify(error='No votes remaining in this category'), 400
        try:
            conn.execute(
                'INSERT INTO votes (beer_id, category, voter_id) VALUES (?, ?, ?)',
                (beer_id, category_id, voter_id)
            )
            conn.commit()
            voted = True
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify(error='Already voted'), 400

    votes_used = conn.execute(
        'SELECT COUNT(*) FROM votes WHERE category=? AND voter_id=?',
        (category_id, voter_id)
    ).fetchone()[0]
    conn.close()

    return jsonify(voted=voted,
                   votes_used=votes_used,
                   votes_remaining=VOTES_PER_CATEGORY - votes_used)


@app.route('/results')
def results():
    if not results_revealed():
        return render_template('results_hidden.html')

    conn = get_db()
    all_results = {}
    for cat_id, cat_name, cat_emoji in CATEGORIES:
        winners = conn.execute('''
            SELECT b.id, b.name, b.guest_name, b.image_path, COUNT(v.id) AS vote_count
            FROM beers b
            JOIN votes v ON b.id = v.beer_id
            WHERE v.category = ?
            GROUP BY b.id
            ORDER BY vote_count DESC
            LIMIT 3
        ''', (cat_id,)).fetchall()
        all_results[cat_id] = {
            'name': cat_name,
            'emoji': cat_emoji,
            'winners': winners,
        }
    conn.close()
    return render_template('results.html', results=all_results, categories=CATEGORIES)


# ---------------------------------------------------------------------------
# Routes – admin
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        flash('Incorrect password.', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/admin')
@require_admin
def admin():
    conn = get_db()
    revealed = conn.execute(
        "SELECT value FROM settings WHERE key='results_revealed'"
    ).fetchone()['value'] == 'true'
    beer_count = conn.execute('SELECT COUNT(*) FROM beers').fetchone()[0]
    vote_count = conn.execute('SELECT COUNT(*) FROM votes').fetchone()[0]

    tallies = []
    for cat_id, cat_name, cat_emoji in CATEGORIES:
        n = conn.execute(
            'SELECT COUNT(*) FROM votes WHERE category=?', (cat_id,)
        ).fetchone()[0]
        tallies.append((cat_id, cat_name, cat_emoji, n))

    all_beers = conn.execute('SELECT * FROM beers ORDER BY guest_name, name').fetchall()
    conn.close()

    return render_template('admin.html',
                           revealed=revealed,
                           beer_count=beer_count,
                           vote_count=vote_count,
                           tallies=tallies,
                           all_beers=all_beers,
                           categories=CATEGORIES)


@app.route('/admin/reveal', methods=['POST'])
@require_admin
def admin_reveal():
    conn = get_db()
    conn.execute(
        "UPDATE settings SET value='true' WHERE key='results_revealed'"
    )
    conn.commit()
    conn.close()
    flash('Results have been revealed! 🎉', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/hide', methods=['POST'])
@require_admin
def admin_hide():
    conn = get_db()
    conn.execute(
        "UPDATE settings SET value='false' WHERE key='results_revealed'"
    )
    conn.commit()
    conn.close()
    flash('Results hidden again.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/delete_beer/<int:beer_id>', methods=['POST'])
@require_admin
def admin_delete_beer(beer_id):
    conn = get_db()
    beer = conn.execute('SELECT image_path FROM beers WHERE id=?', (beer_id,)).fetchone()
    if beer:
        if beer['image_path']:
            try:
                os.remove(os.path.join('static', beer['image_path']))
            except FileNotFoundError:
                pass
        conn.execute('DELETE FROM votes WHERE beer_id=?', (beer_id,))
        conn.execute('DELETE FROM beers WHERE id=?', (beer_id,))
        conn.commit()
        flash('Beer entry deleted.', 'success')
    conn.close()
    return redirect(url_for('admin'))


@app.route('/admin/reset', methods=['POST'])
@require_admin
def admin_reset():
    conn = get_db()
    beers = conn.execute('SELECT image_path FROM beers WHERE image_path IS NOT NULL').fetchall()
    for b in beers:
        try:
            os.remove(os.path.join('static', b['image_path']))
        except FileNotFoundError:
            pass
    conn.execute('DELETE FROM votes')
    conn.execute('DELETE FROM beers')
    conn.execute("UPDATE settings SET value='false' WHERE key='results_revealed'")
    conn.commit()
    conn.close()
    flash('All data has been reset.', 'success')
    return redirect(url_for('admin'))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
