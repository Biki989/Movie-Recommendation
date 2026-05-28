import os
import json
import torch
from preprocessing import preprocess
from train_model import NCFRecommender

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "recommender_model.pt")
HISTORY_PATH = os.path.join(MODEL_DIR, "training_history.json")

os.makedirs(MODEL_DIR, exist_ok=True)

try:
    print("Preprocessing...")
    train_data, test_data, user_enc, movie_enc, n_users, n_movies, _ = preprocess()
    print("Building model...")
    model = NCFRecommender(n_users, n_movies)
    print("Saving model weights...")
    torch.save(model.state_dict(), MODEL_PATH)
    
    history = {
        "loss": [0.5, 0.4, 0.3],
        "val_loss": [0.55, 0.45, 0.35],
        "mae": [0.4, 0.3, 0.2],
        "val_mae": [0.45, 0.35, 0.25]
    }
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f)
    print("Mock train complete.")
except Exception as e:
    import traceback
    traceback.print_exc()
