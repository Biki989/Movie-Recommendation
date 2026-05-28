"""
recommender.py
--------------
Loads the trained NCF model and encoders, then generates movie
recommendations for a given user or via content-based fallback.
"""

import os
import pickle
import numpy as np
import pandas as pd
import torch

from preprocessing import preprocess, get_movie_genres
from train_model import NCFRecommender

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "models", "recommender_model.pt")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "models", "encoders.pkl")

# ── Module-level cache (loaded once per process) ───────────────────────────────
_model        = None
_user_enc     = None
_movie_enc    = None
_n_users      = None
_n_movies     = None
_movies_df    = None
_train_data   = None
_device       = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def _load_artifacts():
    """Load model + encoders into module-level cache (lazy, once)."""
    global _model, _user_enc, _movie_enc, _n_users, _n_movies, _movies_df, _train_data

    if _model is not None:
        return  # already loaded

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. "
            "Run `python train_model.py` first."
        )

    if os.path.exists(ENCODER_PATH):
        with open(ENCODER_PATH, "rb") as f:
            data = pickle.load(f)
        _user_enc   = data["user_enc"]
        _movie_enc  = data["movie_enc"]
        _n_users    = data["n_users"]
        _n_movies   = data["n_movies"]
        _movies_df  = data["movies_df"]
        _train_data = data["train_data"]
    else:
        # Re-run preprocessing to rebuild encoders (slower path)
        train, _, _user_enc, _movie_enc, _n_users, _n_movies, _movies_df = preprocess()
        _train_data = train
        _save_encoders()

    # Load PyTorch model
    _model = NCFRecommender(_n_users, _n_movies)
    _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
    _model.to(_device)
    _model.eval()

    print("[Recommender] Model and encoders loaded.")


def _save_encoders():
    """Persist encoders to disk so subsequent loads are fast."""
    os.makedirs(os.path.dirname(ENCODER_PATH), exist_ok=True)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump({
            "user_enc":   _user_enc,
            "movie_enc":  _movie_enc,
            "n_users":    _n_users,
            "n_movies":   _n_movies,
            "movies_df":  _movies_df,
            "train_data": _train_data,
        }, f)


def is_model_ready() -> bool:
    """Return True if a trained model file exists."""
    return os.path.exists(MODEL_PATH)


def save_encoders_after_training(user_enc, movie_enc, n_users, n_movies,
                                 movies_df, train_data):
    """
    Called by train_model.py after training so encoders are cached
    without needing a separate preprocessing run.
    """
    global _user_enc, _movie_enc, _n_users, _n_movies, _movies_df, _train_data
    _user_enc   = user_enc
    _movie_enc  = movie_enc
    _n_users    = n_users
    _n_movies   = n_movies
    _movies_df  = movies_df
    _train_data = train_data
    _save_encoders()


# ──────────────────────────────────────────────────────────────────────────────
def get_recommendations(user_id: int, top_n: int = 20,
                        genre_filter: str = None) -> list[dict]:
    """
    Generate top-N movie recommendations for a user.

    Parameters
    ----------
    user_id      : internal app user ID (mapped to a MovieLens user)
    top_n        : number of recommendations to return
    genre_filter : optional genre string to filter by

    Returns
    -------
    List of dicts with keys: movieId, title, genres, predicted_rating,
                             confidence_pct, movie_idx
    """
    _load_artifacts()

    # Map app user_id → nearest MovieLens user index (modulo trick)
    user_idx = int(user_id) % _n_users

    # Movies the user has already rated (to exclude from recommendations)
    rated_movie_idxs = set(
        _train_data[_train_data["user_idx"] == user_idx]["movie_idx"].tolist()
    )

    # All movie indices not yet rated by this user
    all_movie_idxs = np.arange(_n_movies)
    unseen_idxs = np.array([m for m in all_movie_idxs if m not in rated_movie_idxs])

    if len(unseen_idxs) == 0:
        unseen_idxs = all_movie_idxs  # fallback: recommend everything

    # Batch predict ratings for all unseen movies
    user_arr  = np.full(len(unseen_idxs), user_idx, dtype=np.int32)
    
    # PyTorch inference
    with torch.no_grad():
        u_t = torch.tensor(user_arr, dtype=torch.long, device=_device)
        m_t = torch.tensor(unseen_idxs, dtype=torch.long, device=_device)
        preds = _model(u_t, m_t).cpu().numpy()
        
    preds = preds.flatten()

    # Sort descending by predicted rating
    sorted_order = np.argsort(preds)[::-1]
    top_idxs  = unseen_idxs[sorted_order]
    top_preds = preds[sorted_order]

    # Build result list from movies_df
    results = []
    for movie_idx, pred_score in zip(top_idxs, top_preds):
        row = _movies_df[_movies_df["movie_idx"] == movie_idx]
        if row.empty:
            continue

        row = row.iloc[0]
        genres = row["genres"]

        # Apply genre filter if requested
        if genre_filter and genre_filter.lower() != "all":
            if genre_filter.lower() not in genres.lower():
                continue

        results.append({
            "movieId":         int(row["movieId"]),
            "title":           row["title"],
            "genres":          genres,
            "predicted_rating": round(float(pred_score) * 5, 2),   # scale back to 0–5
            "confidence_pct":  round(float(pred_score) * 100, 1),  # 0–100 %
            "movie_idx":       int(movie_idx),
        })

        if len(results) >= top_n:
            break

    return results


def get_trending_movies(top_n: int = 12) -> list[dict]:
    """
    Return trending movies based on average predicted ratings across a
    sample of users (lightweight approximation of popularity).
    """
    _load_artifacts()

    # Sample up to 50 users to estimate average predicted rating
    sample_users = np.random.choice(_n_users, size=min(50, _n_users), replace=False)
    all_movie_idxs = np.arange(_n_movies)

    score_sum   = np.zeros(_n_movies, dtype=np.float32)
    score_count = np.zeros(_n_movies, dtype=np.int32)

    with torch.no_grad():
        m_t = torch.tensor(all_movie_idxs, dtype=torch.long, device=_device)
        for u in sample_users:
            u_t = torch.full((_n_movies,), u, dtype=torch.long, device=_device)
            preds = _model(u_t, m_t).cpu().numpy().flatten()
            score_sum   += preds
            score_count += 1

    avg_scores   = score_sum / np.maximum(score_count, 1)
    sorted_order = np.argsort(avg_scores)[::-1][:top_n]

    results = []
    for movie_idx in sorted_order:
        row = _movies_df[_movies_df["movie_idx"] == movie_idx]
        if row.empty:
            continue
        row = row.iloc[0]
        results.append({
            "movieId":   int(row["movieId"]),
            "title":     row["title"],
            "genres":    row["genres"],
            "avg_score": round(float(avg_scores[movie_idx]) * 5, 2),
        })
    return results


def search_movies(query: str, limit: int = 20) -> list[dict]:
    """Search movies by title substring (case-insensitive)."""
    _load_artifacts()
    mask = _movies_df["title"].str.contains(query, case=False, na=False)
    matched = _movies_df[mask].head(limit)
    return matched[["movieId", "title", "genres"]].to_dict(orient="records")


def get_all_genres() -> list[str]:
    """Return sorted list of all unique genres."""
    _load_artifacts()
    return get_movie_genres(_movies_df)
