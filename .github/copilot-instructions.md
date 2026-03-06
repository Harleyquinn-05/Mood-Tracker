# Mood Tracker AI Instructions

## Project Overview
**Mood Tracker** is a Flask-based mental wellness application that detects emotions from user text input and recommends supportive actions or activities. It features user authentication, mood history tracking, and interactive games/exercises (breathing, diary, Ludo, Mario) paired with specific emotional states.

## Architecture & Data Flow

### Core Components
- **[main.py](../mood%20ai/main.py)**: Flask app with all routes, mood analysis logic, and database operations
- **SQLite Database (`app.db`)**: Persists user profiles and mood history; auto-created on first run
- **Templates (Jinja2)**: Server-rendered HTML with embedded JavaScript for interactivity
- **Static Assets**: CSS and images; games use canvas-based implementations

### Key Data Structures
```
Users Table: id, username, email, password_hash
Moods Table: id, user_id, input, emotion, intensity, quote, action, game, created_at
Session: Flask session stores user_id for auth state
```

### Request Flow
1. User submits mood text → POST `/api/mood`
2. Rule-based keyword matching determines emotion class
3. Database stores mood record with suggested action and game mapping
4. Frontend renders quote + action and optionally redirects to game page

## Setup & Development Workflow

### First Time Setup
```bash
cd "mood ai"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate
pip install -r requirements.txt
python main.py
```
App runs in debug mode at `http://127.0.0.1:5000/` with auto-reload.

### Running Tests
```bash
pytest tests/test_api.py
```
Tests verify API endpoints (e.g., `/api/mood` message routing, error handling).

### Environment Variables
- `FLASK_SECRET_KEY`: Required for production sessions; use `os.environ.get()` as fallback
- Database path: Hard-coded to `mood ai/app.db`

## Critical Implementation Patterns

### Mood Classification (Rule-Based)
Located in `get_mood_response()` at [main.py lines 270–400](../mood%20ai/main.py#L320):
- **Input**: User text → lowercased for keyword matching
- **Logic**: Nested if/elif with multiple keyword triggers per emotion
- **Output**: Tuple of (emotion, intensity, quote, action, game name)
- **Example**: "bored" → emotion="boredom", game="ludo"
- **Fallback**: If no keywords match, emotion="unknown" with generic supportive message

### Emotion-to-Game Mapping
| Emotion | Game/Exercise |
|---------|---|
| fear, anxiety | breathing |
| sadness, grief | diary |
| happiness | mario |
| boredom | ludo |
| motivation | todo |
| others | diary |

### Database Access Pattern
Always use context manager for connections:
```python
conn = get_db()
cur = conn.cursor()
try:
    # execute queries
    conn.commit()
finally:
    conn.close()
```
Fallback to in-memory `mood_history` list if DB write fails (guest mode).

### Session & Auth
- Session stored in Flask memory; requires `FLASK_SECRET_KEY` for production
- `user_id` in session determines auth state (None = guest)
- Routes check `session.get('user_id')` and redirect to login if needed
- Password hashing uses Werkzeug's `generate_password_hash()` and `check_password_hash()`

## Key Routes & API

### Web Routes
- `GET /` - Landing page; shows user if logged in
- `GET/POST /register`, `/login`, `/logout` - Auth flows
- `GET /history` - Paginated mood history (server-side, params: `page`, `page_size`)
- `GET /breathing`, `/diary`, `/todo`, `/ludo`, `/mario` - Activity pages

### API Endpoints
- `POST /api/mood` - Detect emotion from text (body: `{"mood": "text"}`); returns emotion, intensity, quote, action, game
- `GET /api/history` - JSON mood list for current user (pagination via `limit`, `before` ISO timestamp)
- `GET /api/profiles` - List all registered usernames
- `POST /switch-profile/<user_id>` - Session hijacking (admin feature?)
- `POST /api/clear-chat` - Delete all moods for user or clear guest in-memory

## Adding New Features

### Adding a New Emotion
1. Edit `get_mood_response()` function in [main.py](../mood%20ai/main.py)
2. Add new `elif` block with keywords for the emotion
3. Assign emotion, intensity, quote, action, and game (ensure game template exists)
4. Test with curl: `curl -X POST http://localhost:5000/api/mood -H "Content-Type: application/json" -d '{"mood":"<keyword>"}'`

### Adding a New Game
1. Create template in `templates/<game_name>.html`
2. Add route in [main.py](../mood%20ai/main.py): `@app.route("/<game_name>")` → `render_template`
3. Link emotion to game in classification logic (modify game assignment in `get_mood_response()`)
4. Update header navigation if needed

### Database Changes
- **Modifying schema**: Edit `init_db()` function; delete `app.db` to reset
- **Migrations**: Currently manual; future: use Flask-Migrate + SQLAlchemy
- **Querying**: Use parameterized queries (?) to prevent SQL injection

## Common Pitfalls & Gotchas

- **Game popups**: Browser popups may be blocked; app falls back to tab navigation
- **Database initialization**: `init_db()` only runs if `app.db` missing; manual deletion needed for schema changes
- **Scalability**: SQLite adequate for single-user/testing; production should use PostgreSQL + connection pooling
- **Session persistence**: In-memory storage lost on app restart; production requires Redis session backend
- **Mood history**: Older entries sorted first in history view, newest first in API (`ORDER BY created_at ASC` vs `DESC`)

## Testing Strategy
- Unit tests in [tests/test_api.py](../mood%20ai/tests/test_api.py) cover API contract (status codes, JSON shape)
- Manual acceptance tests: run app, register, submit moods, verify game routing
- No integration tests for database; tests use `app.config['TESTING']`
