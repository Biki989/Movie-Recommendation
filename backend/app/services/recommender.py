import os
import pickle
import numpy as np
import pandas as pd

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from app.config import settings
from app.services.preprocessing import get_movie_genres

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH   = os.path.join(settings.BASE_DIR, "..", "models", "recommender_model.pt")
WEIGHTS_PATH = os.path.join(settings.BASE_DIR, "..", "models", "ncf_weights.pkl")
ENCODER_PATH = os.path.join(settings.BASE_DIR, "..", "models", "encoders.pkl")

# ── Hyper-parameters ──────────────────────────────────────────────────────────
EMBEDDING_DIM = 50
DENSE_UNITS   = [256, 128, 64]
DROPOUT_RATE  = 0.3

# ── Pure Numpy NCF Recommender for high-performance CPU inference ──────────────
class NumpyNCFRecommender:
    def __init__(self, weights):
        self.weights = weights
        
    def forward(self, user_idx, movie_idx):
        # 1. Embedding lookup
        user_vec = self.weights["user_embedding.weight"][user_idx] # shape (N, 50)
        movie_vec = self.weights["movie_embedding.weight"][movie_idx] # shape (N, 50)
        
        if user_vec.ndim == 1:
            user_vec = np.tile(user_vec, (len(movie_idx), 1))
            
        x = np.concatenate([user_vec, movie_vec], axis=1) # shape (N, 100)
        
        # Dense Layer 0 (Linear)
        w0 = self.weights["dense_layers.0.weight"] # shape (256, 100)
        b0 = self.weights["dense_layers.0.bias"] # shape (256,)
        x = np.dot(x, w0.T) + b0 # shape (N, 256)
        
        # Dense Layer 1 (BatchNorm1d)
        mean1 = self.weights["dense_layers.1.running_mean"]
        var1 = self.weights["dense_layers.1.running_var"]
        weight1 = self.weights["dense_layers.1.weight"]
        bias1 = self.weights["dense_layers.1.bias"]
        eps = 1e-5
        x = (x - mean1) / np.sqrt(var1 + eps) * weight1 + bias1
        
        # Dense Layer 2 (ReLU)
        x = np.maximum(x, 0)
        
        # Dense Layer 4 (Linear)
        w4 = self.weights["dense_layers.4.weight"] # shape (128, 256)
        b4 = self.weights["dense_layers.4.bias"] # shape (128,)
        x = np.dot(x, w4.T) + b4
        
        # Dense Layer 5 (BatchNorm1d)
        mean5 = self.weights["dense_layers.5.running_mean"]
        var5 = self.weights["dense_layers.5.running_var"]
        weight5 = self.weights["dense_layers.5.weight"]
        bias5 = self.weights["dense_layers.5.bias"]
        x = (x - mean5) / np.sqrt(var5 + eps) * weight5 + bias5
        
        # Dense Layer 6 (ReLU)
        x = np.maximum(x, 0)
        
        # Dense Layer 8 (Linear)
        w8 = self.weights["dense_layers.8.weight"] # shape (64, 128)
        b8 = self.weights["dense_layers.8.bias"] # shape (64,)
        x = np.dot(x, w8.T) + b8
        
        # Dense Layer 9 (BatchNorm1d)
        mean9 = self.weights["dense_layers.9.running_mean"]
        var9 = self.weights["dense_layers.9.running_var"]
        weight9 = self.weights["dense_layers.9.weight"]
        bias9 = self.weights["dense_layers.9.bias"]
        x = (x - mean9) / np.sqrt(var9 + eps) * weight9 + bias9
        
        # Dense Layer 10 (ReLU)
        x = np.maximum(x, 0)
        
        # Output Layer 0 (Linear)
        w_out = self.weights["output_layer.0.weight"] # shape (1, 64)
        b_out = self.weights["output_layer.0.bias"] # shape (1,)
        x = np.dot(x, w_out.T) + b_out # shape (N, 1)
        
        # Output Layer 1 (Sigmoid)
        out = 1.0 / (1.0 + np.exp(-x))
        return out.squeeze()


# ── PyTorch NCF Model Definition (Conditional) ───────────────────────────────
if HAS_TORCH:
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
else:
    NCFRecommender = None


# ── Module-level cache ─────────────────────────────────────────────────────────
_model        = None
_user_enc     = None
_movie_enc    = None
_n_users      = None
_n_movies     = None
_movies_df    = None
_train_data   = None
_device       = "cpu"

if HAS_TORCH:
    _device   = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_artifacts():
    """Load model + encoders into module-level cache (lazy, once)."""
    global _model, _user_enc, _movie_enc, _n_users, _n_movies, _movies_df, _train_data

    if _model is not None:
        return  # already loaded

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
        if HAS_TORCH:
            from app.services.preprocessing import preprocess
            train, _, _user_enc, _movie_enc, _n_users, _n_movies, _movies_df = preprocess()
            _train_data = train
            _save_encoders()
        else:
            raise FileNotFoundError(
                f"Encoders not found at {ENCODER_PATH} and preprocessing cannot run without scikit-learn."
            )

    # Auto-convert .pt PyTorch model weights to standard numpy pickle if torch is available
    if not os.path.exists(WEIGHTS_PATH) and os.path.exists(MODEL_PATH) and HAS_TORCH:
        print("[Recommender] Auto-converting recommender_model.pt to ncf_weights.pkl...")
        try:
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
            numpy_weights = {k: v.numpy() for k, v in state_dict.items()}
            os.makedirs(os.path.dirname(WEIGHTS_PATH), exist_ok=True)
            with open(WEIGHTS_PATH, "wb") as f:
                pickle.dump(numpy_weights, f)
        except Exception as e:
            print(f"[Recommender] Failed to auto-convert PyTorch model to Numpy: {e}")

    # Load high-performance Numpy model
    if os.path.exists(WEIGHTS_PATH):
        with open(WEIGHTS_PATH, "rb") as f:
            weights = pickle.load(f)
        _model = NumpyNCFRecommender(weights)
        print("[Recommender] Numpy-based NCF model loaded successfully.")
    elif os.path.exists(MODEL_PATH) and HAS_TORCH:
        # Fallback to PyTorch model
        _model = NCFRecommender(_n_users, _n_movies)
        _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
        _model.to(_device)
        _model.eval()
        print("[Recommender] PyTorch-based NCF model loaded successfully (Fallback).")
    else:
        raise FileNotFoundError(
            f"Trained model weights not found at {WEIGHTS_PATH} or {MODEL_PATH}."
        )


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
    return os.path.exists(WEIGHTS_PATH) or os.path.exists(MODEL_PATH)


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
    """Generate top-N movie recommendations using NCF inference."""
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
    
    if isinstance(_model, NumpyNCFRecommender):
        preds = _model.forward(user_arr, unseen_idxs)
    else:
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

    if isinstance(_model, NumpyNCFRecommender):
        for u in sample_users:
            preds = _model.forward(u, all_movie_idxs).flatten()
            score_sum   += preds
            score_count += 1
    else:
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
