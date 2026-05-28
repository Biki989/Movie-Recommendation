"""
preprocessing.py
----------------
Handles loading, cleaning, and encoding the MovieLens dataset.
Produces encoded user/movie indices and normalized ratings ready for model training.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MOVIES_PATH = os.path.join(DATA_DIR, "movies.csv")
RATINGS_PATH = os.path.join(DATA_DIR, "ratings.csv")


def load_data():
    """Load movies.csv and ratings.csv from the data/ directory."""
    movies = pd.read_csv(MOVIES_PATH)
    ratings = pd.read_csv(RATINGS_PATH)
    return movies, ratings


def preprocess(test_size: float = 0.2, random_state: int = 42):
    """
    Full preprocessing pipeline.

    Returns
    -------
    train_data, test_data  : DataFrames with encoded columns
    user_encoder           : fitted LabelEncoder for user IDs
    movie_encoder          : fitted LabelEncoder for movie IDs
    n_users, n_movies      : vocabulary sizes for embedding layers
    movies_df              : cleaned movies DataFrame
    """
    movies, ratings = load_data()

    # ── Drop duplicates & missing values ──────────────────────────────────────
    ratings = ratings.dropna(subset=["userId", "movieId", "rating"])
    ratings = ratings.drop_duplicates()

    # Keep only movies that appear in both files
    valid_movie_ids = set(movies["movieId"].unique())
    ratings = ratings[ratings["movieId"].isin(valid_movie_ids)]

    # ── Encode IDs to contiguous integers ────────────────────────────────────
    user_encoder = LabelEncoder()
    movie_encoder = LabelEncoder()

    ratings["user_idx"] = user_encoder.fit_transform(ratings["userId"])
    ratings["movie_idx"] = movie_encoder.fit_transform(ratings["movieId"])

    # ── Normalize ratings to [0, 1] ──────────────────────────────────────────
    min_rating = ratings["rating"].min()
    max_rating = ratings["rating"].max()
    ratings["rating_norm"] = (ratings["rating"] - min_rating) / (max_rating - min_rating)

    n_users = ratings["user_idx"].nunique()
    n_movies = ratings["movie_idx"].nunique()

    # ── Train / test split ───────────────────────────────────────────────────
    train_data, test_data = train_test_split(
        ratings, test_size=test_size, random_state=random_state
    )

    # ── Enrich movies with encoded index ─────────────────────────────────────
    # Only keep movies that exist in ratings (after filtering)
    present_ids = movie_encoder.classes_  # original movieIds that were encoded
    movies_df = movies[movies["movieId"].isin(present_ids)].copy()
    movies_df["movie_idx"] = movie_encoder.transform(movies_df["movieId"])

    print(f"[Preprocessing] Users: {n_users} | Movies: {n_movies} | Ratings: {len(ratings)}")
    return train_data, test_data, user_encoder, movie_encoder, n_users, n_movies, movies_df


def get_movie_genres(movies_df: pd.DataFrame):
    """Return a deduplicated list of all genres found in the dataset."""
    all_genres = set()
    for genre_str in movies_df["genres"].dropna():
        for g in genre_str.split("|"):
            if g.strip() and g.strip() != "(no genres listed)":
                all_genres.add(g.strip())
    return sorted(all_genres)


if __name__ == "__main__":
    train, test, ue, me, nu, nm, mvs = preprocess()
    print(f"Train: {len(train)} | Test: {len(test)}")
    print(f"Sample genres: {get_movie_genres(mvs)[:5]}")
