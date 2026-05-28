import os
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from app.config import settings
from app.services.preprocessing import preprocess, get_movie_genres

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(settings.BASE_DIR, "..", "models", "recommender_model.pt")
ENCODER_PATH = os.path.join(settings.BASE_DIR, "..", "models", "encoders.pkl")

# ── Hyper-parameters ──────────────────────────────────────────────────────────
EMBEDDING_DIM = 50
DENSE_UNITS   = [256, 128, 64]
DROPOUT_RATE  = 0.3

# ── NCF model definition ───────────────────────────────────────────────────────
class NCFRecommender(nn.Module):
    def __init__(self, n_users, n_movies, embedding_dim=EMBEDDING_DIM):
        super(NCFRecommender, self).__init__()
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.movie_embedding = nn.Embedding(n_movies, embedding_dim)
        
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.movie_embedding.weight, std=0.01)
        
        layers = []
        input_dim = embedding_dim * 2
        for units in DENSE_UNITS:
            layers.append(nn.Linear(input_dim, units))
            layers.append(nn.BatchNorm1d(units))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(DROPOUT_RATE))
            input_dim = units
            
        self.dense_layers = nn.Sequential(*layers)
        self.output_layer = nn.Sequential(
            nn.Linear(input_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, user_idx, movie_idx):
        user_vec = self.user_embedding(user_idx)
        movie_vec = self.movie_embedding(movie_idx)
        x = torch.cat([user_vec, movie_vec], dim=1)
        x = self.dense_layers(x)
        out = self.output_layer(x)
        return out.squeeze()


# ── Module-level cache ─────────────────────────────────────────────────────────
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
            "Please run model training first."
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
        # Re-run preprocessing to rebuild encoders
        train, _, _user_enc, _movie_enc, _n_users, _n_movies, _movies_df = preprocess()
        _train_data = train
        _save_encoders()

    # Load PyTorch model
    _model = NCFRecommender(_n_users, _n_movies)
    _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
    _model.to(_device)
    _model.eval()

    print("[Recommender] Model and encoders loaded successfully.")


def _save_encoders():
    """Persist encoders to disk."""
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
    """Called after background training to cache fitting encoders."""
    global _user_enc, _movie_enc, _n_users, _n_movies, _movies_df, _train_data
    _user_enc   = user_enc
    _movie_enc  = movie_enc
    _n_users    = n_users
    _n_movies   = n_movies
    _movies_df  = movies_df
    _train_data = train_data
    _save_encoders()


def force_reload_model():
    """Force reloading model state from disk (called after retraining)."""
    global _model
    _model = None
    _load_artifacts()


def get_recommendations(user_id: int, top_n: int = 20,
                         genre_filter: str = None) -> list[dict]:
    """Generate top-N movie recommendations using PyTorch NCF inference."""
    _load_artifacts()

    # Map app user_id → nearest MovieLens user index (modulo trick)
    user_idx = int(user_id) % _n_users

    # Movies the user has already rated (exclude from recommendations)
    rated_movie_idxs = set(
        _train_data[_train_data["user_idx"] == user_idx]["movie_idx"].tolist()
    )

    all_movie_idxs = np.arange(_n_movies)
    unseen_idxs = np.array([m for m in all_movie_idxs if m not in rated_movie_idxs])

    if len(unseen_idxs) == 0:
        unseen_idxs = all_movie_idxs  # fallback: recommend everything

    # Batch predict ratings
    user_arr  = np.full(len(unseen_idxs), user_idx, dtype=np.int32)
    
    with torch.no_grad():
        u_t = torch.tensor(user_arr, dtype=torch.long, device=_device)
        m_t = torch.tensor(unseen_idxs, dtype=torch.long, device=_device)
        preds = _model(u_t, m_t).cpu().numpy()
        
    preds = preds.flatten()

    sorted_order = np.argsort(preds)[::-1]
    top_idxs  = unseen_idxs[sorted_order]
    top_preds = preds[sorted_order]

    results = []
    for movie_idx, pred_score in zip(top_idxs, top_preds):
        row = _movies_df[_movies_df["movie_idx"] == movie_idx]
        if row.empty:
            continue

        row = row.iloc[0]
        genres = row["genres"]

        if genre_filter and genre_filter.lower() != "all":
            if genre_filter.lower() not in genres.lower():
                continue

        results.append({
            "movieId":         int(row["movieId"]),
            "title":           row["title"],
            "genres":          genres,
            "predicted_rating": round(float(pred_score) * 5, 2),   # scale back to 0-5
            "confidence_pct":  round(float(pred_score) * 100, 1),  # 0-100 %
            "movie_idx":       int(movie_idx),
        })

        if len(results) >= top_n:
            break

    return results


def get_trending_movies(top_n: int = 12) -> list[dict]:
    """Calculate trending movies using average predictions over sampled users."""
    _load_artifacts()

    # Sample up to 50 users
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
            "confidence_pct": round(float(avg_scores[movie_idx]) * 100, 1),
        })
    return results


def search_movies(query: str, limit: int = 20) -> list[dict]:
    """Search movies by title substring (case-insensitive)."""
    _load_artifacts()
    mask = _movies_df["title"].str.contains(query, case=False, na=False)
    matched = _movies_df[mask].head(limit)
    return matched[["movieId", "title", "genres"]].to_dict(orient="records")


def get_all_genres() -> list[str]:
    """Return unique genres present in system."""
    _load_artifacts()
    return get_movie_genres(_movies_df)
