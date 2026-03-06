from flask import Flask, request, render_template, jsonify, session, redirect, url_for, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# In-memory storage for moods and responses
mood_history = []

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")



def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            input TEXT,
            emotion TEXT,
            intensity TEXT,
            quote TEXT,
            action TEXT,
            game TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

        cur.execute("""
        CREATE TABLE security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            ip_address TEXT,
            created_at TEXT
        );
        """)

        conn.commit()
        conn.close()


# ensure DB exists on startup
init_db()
   
@app.route("/")
def index():
    user = None
    if 'user_id' in session:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        conn.close()
    return render_template("index.html", user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not email or not password:
            flash('Please provide username, email, and password')
            return redirect(url_for('register'))

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                        (username, email, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful — please log in')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            if 'email' in str(e):
                flash('Email already registered')
            else:
                flash('Username already taken')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])


def login():

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        cur = conn.cursor()
        # Try to find user by username or email (if email is provided)
        if email:
            cur.execute('SELECT id, password_hash FROM users WHERE username = ? OR email = ?', (username, email))
        else:
            cur.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            flash('Logged in')
            return redirect(url_for('index'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    user_id = session.get('user_id')

    if user_id:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()

        if user:
            cur.execute(
                "INSERT INTO security_logs (username, action, ip_address, created_at) VALUES (?, ?, ?, ?)",
                (user['username'], "LOGOUT", request.remote_addr, datetime.utcnow().isoformat())
            )
            conn.commit()

        conn.close()

    session.pop('user_id', None)
    flash('Logged out')
    return redirect(url_for('index'))


@app.route('/history')
def history():
    if 'user_id' not in session:
        flash('Please log in to see your history')
        return redirect(url_for('login'))
    # server-side pagination: ?page=1&page_size=12
    try:
        page = int(request.args.get('page', 1))
    except Exception:
        page = 1
    try:
        page_size = int(request.args.get('page_size', 12))
    except Exception:
        page_size = 12
    page = max(1, page)
    page_size = max(1, min(page_size, 200))

    conn = get_db()
    cur = conn.cursor()
    # total count for the user
    cur.execute('SELECT COUNT(*) as cnt FROM moods WHERE user_id = ?', (session['user_id'],))
    row = cur.fetchone()
    if row is not None:
        try:
            total = row['cnt']
        except Exception:
            total = row[0]
    else:
        total = 0

    offset = (page - 1) * page_size
    cur.execute('SELECT * FROM moods WHERE user_id = ? ORDER BY created_at ASC, id ASC LIMIT ? OFFSET ?', (session['user_id'], page_size, offset))
    rows = cur.fetchall()
    conn.close()

    total_pages = (total + page_size - 1) // page_size if total is not None and page_size > 0 else 1

    return render_template('history.html', moods=rows, page=page, page_size=page_size, total=total, total_pages=total_pages)


@app.route('/api/history')
def api_history():
    """Return the signed-in user's mood history as JSON (oldest first).
    If the user is not logged in, return an empty list.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])
    # pagination parameters
    try:
        limit = int(request.args.get('limit', 20))
    except Exception:
        limit = 20
    limit = max(1, min(limit, 100))
    before = request.args.get('before')  # ISO timestamp

    conn = get_db()
    cur = conn.cursor()

    if before:
        # return items older than 'before' (newest first)
        cur.execute('''
            SELECT id, input, emotion, intensity, quote, action, game, created_at
            FROM moods
            WHERE user_id = ? AND created_at < ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        ''', (user_id, before, limit))
    else:
        cur.execute('''
            SELECT id, input, emotion, intensity, quote, action, game, created_at
            FROM moods
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        ''', (user_id, limit))

    rows = cur.fetchall()
    conn.close()

    # convert sqlite3.Row to regular dicts (newest-first)
    out = []
    for r in rows:
        out.append({
            'id': r['id'],
            'input': r['input'],
            'emotion': r['emotion'],
            'intensity': r['intensity'],
            'quote': r['quote'],
            'action': r['action'],
            'game': r['game'],
            'created_at': r['created_at']
        })

    has_more = len(out) == limit
    next_before = out[-1]['created_at'] if out else None

    return jsonify({
        'items': out,
        'has_more': has_more,
        'next_before': next_before
    })

@app.route("/breathing")
@app.route("/breathing.html")
def breathing():
    return render_template("breathing.html")

@app.route("/todo")
@app.route("/todo.html")
def todo():
    return render_template("todo.html")

@app.route("/diary")
@app.route("/diary.html")
def diary():
    return render_template("diary.html")

# Route for Ludo game
@app.route("/ludo")
@app.route("/ludo.html")
def ludo():
    return render_template("ludo.html")

# Route for Mario-like game
@app.route("/mario")
@app.route("/mario.html")
def mario():
    return render_template("mario.html")

# Route for Breathing exercise game/page




@app.route("/api/mood", methods=["POST"])
def get_mood_response():
    data = request.get_json()
    user_input = data.get("mood", "").strip()

    if not user_input:
        return jsonify({
            "status": "error",
            "emotion": "unknown",
            "intensity": "not specified",
            "quote": "Please describe your situation in detail.",
            "action": "Try writing a short sentence about how you feel.",
            "game": None
        }), 400

    # Expanded rule-based emotion and intensity/description detection
    text = user_input.lower()
    emotion, intensity, quote, action, game = None, None, None, None, None

    if "happy" in text or "joy" in text or "excited" in text or "content" in text:
        emotion = "happiness"
        intensity = "joy, contentment, satisfaction"
        quote = "Happiness is best when shared!"
        action = "Celebrate your joy—share it with someone or do something you love."
        game = "mario"
    elif "sad" in text or "grief" in text or "hopeless" in text or "disappointed" in text:
        if "grief" in text:
            emotion = "grief"
            intensity = "intense sorrow, often from loss"
            quote = "Grief is the price we pay for love."
            action = "Allow yourself to mourn and seek support from loved ones."
            game = "diary"
        else:
            emotion = "sadness"
            intensity = "disappointment, sorrow, or hopelessness"
            quote = "It's okay to feel down. Brighter days are ahead."
            action = "Talk to a friend or write down your feelings."
            game = "diary"
    elif "fear" in text or "afraid" in text or "scared" in text or "terrified" in text:
        emotion = "fear"
        intensity = "worry, nervousness, or terror"
        quote = "Courage is not the absence of fear, but the triumph over it."
        action = "Take deep breaths and remind yourself of your strengths."
        game = "breathing"
    elif "angry" in text or "mad" in text or "furious" in text or "rage" in text:
        emotion = "anger"
        intensity = "frustration, irritation, or rage"
        quote = "Anger is one letter short of danger. Take a deep breath."
        action = "Step away from the situation and do some deep breathing."
        game = "breathing"
    elif "surprise" in text or "shocked" in text or "astonished" in text:
        emotion = "surprise"
        intensity = "unexpected, positive or negative"
        quote = "Life is full of surprises. Embrace the unexpected."
        action = "Pause and process the new information before reacting."
        game = "diary"
    elif "disgust" in text or "revolted" in text or "repulsed" in text:
        emotion = "disgust"
        intensity = "strong aversion or revulsion"
        quote = "Disgust can be a signal to protect yourself."
        action = "Distance yourself from the source and focus on something pleasant."
        game = "diary"
    elif "love" in text or "affection" in text or "caring" in text:
        emotion = "love"
        intensity = "deep affection and care"
        quote = "To love and be loved is the greatest joy."
        action = "Express your feelings to those you care about."
        game = "diary"
    elif "jealous" in text or "jealousy" in text:
        emotion = "jealousy"
        intensity = "envy mixed with resentment"
        quote = "Jealousy is a sign of what you value."
        action = "Reflect on your feelings and communicate openly."
        game = "diary"
    elif "pride" in text or "proud" in text:
        emotion = "pride"
        intensity = "deep satisfaction in achievements"
        quote = "Be proud of how far you’ve come."
        action = "Celebrate your achievements and encourage others."
        game = "diary"
    elif "guilt" in text or "guilty" in text:
        emotion = "guilt"
        intensity = "remorse for actions or inactions"
        quote = "Guilt is a chance to learn and grow."
        action = "Make amends if possible and forgive yourself."
        game = "diary"
    elif "shame" in text or "ashamed" in text:
        emotion = "shame"
        intensity = "painful sense of failure or disgrace"
        quote = "Shame grows in secrecy. Share your feelings with someone you trust."
        action = "Remember, everyone makes mistakes. Practice self-compassion."
        game = "diary"
    elif "anxiety" in text or "anxious" in text or "nervous" in text:
        emotion = "anxiety"
        intensity = "worry, nervousness, unease"
        quote = "Anxiety does not empty tomorrow of its sorrows, but only empties today of its strength."
        action = "Try grounding techniques and focus on the present moment."
        game = "breathing"
    elif "envy" in text or "envious" in text:
        emotion = "envy"
        intensity = "resentful longing for what others have"
        quote = "Envy is the art of counting the other fellow’s blessings instead of your own."
        action = "Focus on your own journey and practice gratitude."
        game = "diary"
    elif "embarrass" in text or "embarrassed" in text or "awkward" in text:
        emotion = "embarrassment"
        intensity = "self-consciousness or awkwardness"
        quote = "Embarrassment is a sign you’re growing."
        action = "Laugh it off and remember everyone feels this way sometimes."
        game = "diary"
    elif "worry" in text or "worried" in text:
        emotion = "worry"
        intensity = "unease about a problem or outcome"
        quote = "Worrying does not take away tomorrow’s troubles, it takes away today’s peace."
        action = "Write down your worries and focus on what you can control."
        game = "breathing"
    elif "bored" in text:
        emotion = "boredom"
        intensity = "lack of interest or stimulation"
        quote = "Boredom is the space in which creativity begins."
        action = "Try a new hobby or call a friend."
        game = "ludo"
    elif "motivated" in text or "working" in text:
        emotion = "motivation"
        intensity = "strong desire to achieve or improve"
        quote = "Motivation is what gets you started. Habit is what keeps you going."
        action = "Set small, achievable goals to build momentum."
        game = "todo"
    else:
        emotion = "unknown"
        intensity = "emotion not recognized"
        quote = "Emotions are valid. Take care of yourself."
        action = "Reflect on your feelings or talk to someone you trust."
        game = None

    # Save to mood history (in DB if user logged in, otherwise keep in-memory)
    created_at = datetime.utcnow().isoformat()
    user_id = session.get('user_id')
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO moods (user_id, input, emotion, intensity, quote, action, game, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, user_input, emotion, intensity, quote, action, game, created_at)
        )
        conn.commit()
        conn.close()
    except Exception:
        # fallback to in-memory if DB fails
        mood_history.append({
            "input": user_input,
            "emotion": emotion,
            "intensity": intensity,
            "quote": quote,
            "action": action,
            "game": game,
            "created_at": created_at,
        })

    return jsonify({
        "status": "success",
        "emotion": emotion,
        "intensity": intensity,
        "quote": quote,
        "action": action,
        "game": game
    })


# API endpoint to get all usernames (for profile switcher)
@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM users ORDER BY username')
    rows = cur.fetchall()
    conn.close()
    profiles = [{'id': r['id'], 'username': r['username']} for r in rows]
    return jsonify({'profiles': profiles})


# Route to switch/login to another profile
@app.route('/switch-profile/<int:user_id>', methods=['POST'])
def switch_profile(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        session['user_id'] = user_id
        return redirect(url_for('index'))
    flash('Profile not found')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, port=5001)

  
@app.route('/admin/security')
def security_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM security_logs ORDER BY created_at DESC")
    logs = cur.fetchall()
    conn.close()
    return render_template("security.html", logs=logs)



# API endpoint to clear chat (new chat button)
@app.route('/api/clear-chat', methods=['POST'])
def clear_chat():
    """Clear the chat history for the current user (or in-memory for guests)."""
    global mood_history
    user_id = session.get('user_id')
    if user_id:
        # Delete from DB for logged-in users
        conn = get_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM moods WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Chat cleared'})
    else:
        # Clear in-memory for guests
        mood_history = []
        return jsonify({'status': 'success', 'message': 'Chat cleared'})
