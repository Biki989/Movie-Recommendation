"""
app.py
------
Main Flask application entry point.
Handles routing, authentication, recommendations, and admin dashboard.
"""

import os
import json
import threading
from datetime import datetime

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, session, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

import recommender as rec

load_dotenv()

# ── App setup ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cinematix-super-secret-key-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# TMDB API key (set in .env or leave blank for placeholder posters)
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"

db           = SQLAlchemy(app)
bcrypt       = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view     = "login"
login_manager.login_message  = "Please log in to access this page."
login_manager.login_message_category = "warning"

# ── Training state (for async retrain endpoint) ────────────────────────────────
_training_status = {"running": False, "message": "idle", "progress": 0}


# ══════════════════════════════════════════════════════════════════════════════
# Database Models
# ══════════════════════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    """Registered application user."""
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings    = db.relationship("UserRating",    backref="user", lazy=True)
    bookmarks  = db.relationship("Bookmark",      backref="user", lazy=True)
    rec_history = db.relationship("RecHistory",   backref="user", lazy=True)


class UserRating(db.Model):
    """Movie rating submitted by a user inside the app."""
    __tablename__ = "user_ratings"
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    title    = db.Column(db.String(200))
    genres   = db.Column(db.String(200))
    rating   = db.Column(db.Float, nullable=False)
    rated_at = db.Column(db.DateTime, default=datetime.utcnow)


class Bookmark(db.Model):
    """User's bookmarked / favorited movies."""
    __tablename__ = "bookmarks"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id     = db.Column(db.Integer, nullable=False)
    title        = db.Column(db.String(200))
    genres       = db.Column(db.String(200))
    bookmarked_at = db.Column(db.DateTime, default=datetime.utcnow)


class RecHistory(db.Model):
    """Recommendation history for a user."""
    __tablename__ = "rec_history"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id     = db.Column(db.Integer, nullable=False)
    title        = db.Column(db.String(200))
    genres       = db.Column(db.String(200))
    confidence   = db.Column(db.Float)
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def fetch_poster(title: str) -> str:
    """Fetch movie poster URL from TMDB. Returns a placeholder on failure."""
    if not TMDB_API_KEY:
        return url_for("static", filename="images/placeholder.png")
    try:
        import requests as _req
        resp = _req.get(
            f"{TMDB_BASE}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": title, "language": "en-US"},
            timeout=3
        )
        data = resp.json()
        results = data.get("results", [])
        if results and results[0].get("poster_path"):
            return TMDB_IMG + results[0]["poster_path"]
    except Exception:
        pass
    return url_for("static", filename="images/placeholder.png")


def enrich_with_posters(movie_list: list) -> list:
    """Add poster_url key to each movie dict."""
    for m in movie_list:
        m["poster_url"] = fetch_poster(m["title"])
    return movie_list


def save_rec_history(user_id: int, recommendations: list):
    """Persist the latest recommendation batch to the DB."""
    for r in recommendations[:10]:
        entry = RecHistory(
            user_id    = user_id,
            movie_id   = r["movieId"],
            title      = r["title"],
            genres     = r["genres"],
            confidence = r.get("confidence_pct", 0),
        )
        db.session.add(entry)
    db.session.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Routes – Auth
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Homepage: hero banner + trending movies."""
    trending = []
    model_ready = rec.is_model_ready()
    if model_ready:
        try:
            trending = rec.get_trending_movies(top_n=48)
            enrich_with_posters(trending)
        except Exception as e:
            flash(f"Could not load trending movies: {e}", "warning")
    genres = rec.get_all_genres() if model_ready else []
    return render_template("index.html", trending=trending,
                           genres=genres, model_ready=model_ready)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("recommendations"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}! 🎬", "success")
            return redirect(request.args.get("next") or url_for("recommendations"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("recommendations"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        else:
            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            user   = User(username=username, email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created! Let's find your movies. 🎬", "success")
            return redirect(url_for("recommendations"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


# ══════════════════════════════════════════════════════════════════════════════
# Routes – Recommendations
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/recommendations")
@login_required
def recommendations():
    """Personalized recommendations page."""
    if not rec.is_model_ready():
        flash("Model not trained yet. Ask an admin to train the model.", "warning")
        return render_template("recommendations.html",
                               recs=[], genres=[], genre_filter="All")

    genre_filter = request.args.get("genre", "All")
    try:
        movie_recs = rec.get_recommendations(
            user_id=current_user.id,
            top_n=24,
            genre_filter=genre_filter if genre_filter != "All" else None
        )
        enrich_with_posters(movie_recs)
        save_rec_history(current_user.id, movie_recs)
    except Exception as e:
        flash(f"Recommendation error: {e}", "danger")
        movie_recs = []

    genres = rec.get_all_genres()
    return render_template("recommendations.html",
                           recs=movie_recs, genres=genres,
                           genre_filter=genre_filter)


@app.route("/search")
@login_required
def search():
    """Movie search endpoint."""
    query  = request.args.get("q", "").strip()
    movies = []
    if query:
        try:
            movies = rec.search_movies(query, limit=24)
            enrich_with_posters(movies)
        except Exception as e:
            flash(f"Search error: {e}", "danger")
    genres = rec.get_all_genres() if rec.is_model_ready() else []
    return render_template("search.html", movies=movies,
                           query=query, genres=genres)


# ══════════════════════════════════════════════════════════════════════════════
# Routes – User Actions (AJAX-friendly)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/rate", methods=["POST"])
@login_required
def rate_movie():
    """Submit a rating for a movie."""
    data     = request.get_json(silent=True) or request.form
    movie_id = data.get("movie_id")
    title    = data.get("title", "")
    genres   = data.get("genres", "")
    rating   = data.get("rating")

    if not movie_id or not rating:
        return jsonify({"success": False, "message": "movie_id and rating required"}), 400

    try:
        rating = float(rating)
        if not (0.5 <= rating <= 5.0):
            raise ValueError
    except ValueError:
        return jsonify({"success": False, "message": "Rating must be 0.5–5.0"}), 400

    # Upsert rating
    existing = UserRating.query.filter_by(
        user_id=current_user.id, movie_id=int(movie_id)
    ).first()
    if existing:
        existing.rating  = rating
        existing.rated_at = datetime.utcnow()
    else:
        db.session.add(UserRating(
            user_id=current_user.id, movie_id=int(movie_id),
            title=title, genres=genres, rating=rating
        ))
    db.session.commit()
    return jsonify({"success": True, "message": f"Rated {title} → {rating} ⭐"})


@app.route("/bookmark", methods=["POST"])
@login_required
def toggle_bookmark():
    """Toggle bookmark state for a movie."""
    data     = request.get_json(silent=True) or request.form
    movie_id = int(data.get("movie_id", 0))
    title    = data.get("title", "")
    genres   = data.get("genres", "")

    existing = Bookmark.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "bookmarked": False})
    else:
        db.session.add(Bookmark(user_id=current_user.id, movie_id=movie_id,
                                title=title, genres=genres))
        db.session.commit()
        return jsonify({"success": True, "bookmarked": True})


@app.route("/bookmarks")
@login_required
def bookmarks():
    """User's bookmarked movies."""
    bmarks = Bookmark.query.filter_by(user_id=current_user.id)\
                           .order_by(Bookmark.bookmarked_at.desc()).all()
    enriched = []
    for b in bmarks:
        enriched.append({
            "movieId":    b.movie_id,
            "title":      b.title,
            "genres":     b.genres,
            "poster_url": fetch_poster(b.title),
            "bookmarked_at": b.bookmarked_at.strftime("%b %d, %Y"),
        })
    return render_template("bookmarks.html", bookmarks=enriched)


@app.route("/history")
@login_required
def history():
    """User's recommendation history."""
    hist = RecHistory.query.filter_by(user_id=current_user.id)\
                           .order_by(RecHistory.recommended_at.desc())\
                           .limit(50).all()
    enriched = []
    for h in hist:
        enriched.append({
            "movieId":    h.movie_id,
            "title":      h.title,
            "genres":     h.genres,
            "confidence": h.confidence,
            "poster_url": fetch_poster(h.title),
            "recommended_at": h.recommended_at.strftime("%b %d, %Y %H:%M"),
        })
    return render_template("history.html", history=enriched)


# ══════════════════════════════════════════════════════════════════════════════
# Routes – Admin Dashboard
# ══════════════════════════════════════════════════════════════════════════════

def _admin_required(f):
    """Decorator: block non-admin users."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.route("/dashboard")
@login_required
@_admin_required
def dashboard():
    """Admin dashboard: stats + training controls."""
    import os, json as _json
    history_path = os.path.join(BASE_DIR, "models", "training_history.json")
    plot_path    = os.path.join(BASE_DIR, "models", "training_plot.png")

    history_data = {}
    if os.path.exists(history_path):
        with open(history_path) as f:
            history_data = _json.load(f)

    stats = {
        "total_users":   User.query.count(),
        "total_ratings": UserRating.query.count(),
        "total_bookmarks": Bookmark.query.count(),
        "model_ready":   rec.is_model_ready(),
        "plot_exists":   os.path.exists(plot_path),
    }
    return render_template("dashboard.html",
                           stats=stats,
                           history_data=json.dumps(history_data),
                           training_status=_training_status)


@app.route("/admin/retrain", methods=["POST"])
@login_required
@_admin_required
def retrain():
    """Trigger async model retraining."""
    global _training_status
    if _training_status["running"]:
        return jsonify({"success": False, "message": "Training already in progress"}), 409

    def _train_job():
        global _training_status
        _training_status = {"running": True, "message": "Preprocessing data…", "progress": 10}
        try:
            from train_model import train
            _training_status["message"] = "Training model…"
            _training_status["progress"] = 30
            model, ue, me, nu, nm = train()
            # Reload recommender artifacts
            from preprocessing import preprocess
            train_data, _, _, _, _, _, movies_df = preprocess()
            rec.save_encoders_after_training(ue, me, nu, nm, movies_df, train_data)
            # Reload model in recommender module
            rec._model = None
            _training_status = {"running": False, "message": "Training complete! ✅", "progress": 100}
        except Exception as e:
            _training_status = {"running": False, "message": f"Error: {e}", "progress": 0}

    thread = threading.Thread(target=_train_job, daemon=True)
    thread.start()
    return jsonify({"success": True, "message": "Training started in background."})


@app.route("/admin/training-status")
@login_required
@_admin_required
def training_status():
    """Poll training progress."""
    return jsonify(_training_status)


# ══════════════════════════════════════════════════════════════════════════════
# API Endpoints (AJAX)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/recommendations")
@login_required
def api_recommendations():
    """JSON recommendations endpoint for AJAX calls."""
    genre  = request.args.get("genre")
    top_n  = int(request.args.get("top_n", 12))
    if not rec.is_model_ready():
        return jsonify({"error": "Model not ready"}), 503
    try:
        recs = rec.get_recommendations(current_user.id, top_n=top_n,
                                       genre_filter=genre)
        return jsonify(recs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search")
def api_search():
    """JSON search endpoint."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    try:
        results = rec.search_movies(query, limit=10)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/trending")
def api_trending():
    """JSON trending movies."""
    if not rec.is_model_ready():
        return jsonify([])
    try:
        return jsonify(rec.get_trending_movies(top_n=10))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# Error Handlers
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ══════════════════════════════════════════════════════════════════════════════
# Startup
# ══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    # Create default admin if none exists
    if not User.query.filter_by(is_admin=True).first():
        admin_pw = bcrypt.generate_password_hash("admin123").decode("utf-8")
        admin    = User(username="admin", email="admin@cinematix.ai",
                        password=admin_pw, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print("[App] Default admin created -> admin@cinematix.ai / admin123")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
