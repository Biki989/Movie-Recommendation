import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from app.config import settings
from app.services.preprocessing import preprocess
from app.services.recommender import NCFRecommender, MODEL_PATH, ENCODER_PATH, save_encoders_after_training

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.dirname(MODEL_PATH)
HISTORY_PATH = os.path.join(MODEL_DIR, "training_history.json")
PLOT_PATH = os.path.join(MODEL_DIR, "training_plot.png")

# ── Hyper-parameters ──────────────────────────────────────────────────────────
EMBEDDING_DIM = 50
LEARNING_RATE = 0.001
BATCH_SIZE    = 512
EPOCHS        = 10

class RatingsDataset(Dataset):
    def __init__(self, user_indices, movie_indices, ratings):
        self.user_indices = torch.tensor(user_indices, dtype=torch.long)
        self.movie_indices = torch.tensor(movie_indices, dtype=torch.long)
        self.ratings = torch.tensor(ratings, dtype=torch.float32)

    def __len__(self):
        return len(self.ratings)

    def __getitem__(self, idx):
        return self.user_indices[idx], self.movie_indices[idx], self.ratings[idx]


def train_model(progress_callback=None):
    """
    Standard PyTorch training pipeline with callback reporting.
    Runs completely in background to keep API thread responsive.
    """
    if progress_callback:
        progress_callback("Preprocessing dataset…", 10)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. Preprocess
    train_data, test_data, user_enc, movie_enc, n_users, n_movies, movies_df = preprocess()
    
    # 2. Build model
    model = NCFRecommender(n_users, n_movies).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-6)

    # 3. Dataloaders
    train_dataset = RatingsDataset(
        train_data["user_idx"].values,
        train_data["movie_idx"].values,
        train_data["rating_norm"].values
    )
    test_dataset = RatingsDataset(
        test_data["user_idx"].values,
        test_data["movie_idx"].values,
        test_data["rating_norm"].values
    )

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    history = {"loss": [], "val_loss": [], "mae": [], "val_mae": []}
    best_val_loss = float("inf")
    patience = 3
    patience_counter = 0

    # 4. Training loop
    for epoch in range(EPOCHS):
        if progress_callback:
            progress_callback(f"Training Epoch {epoch+1}/{EPOCHS}…", int(20 + (epoch / EPOCHS) * 60))
            
        model.train()
        train_loss = 0.0
        train_mae = 0.0
        
        for users, movies, ratings in train_loader:
            users, movies, ratings = users.to(device), movies.to(device), ratings.to(device)
            
            optimizer.zero_grad()
            outputs = model(users, movies)
            loss = criterion(outputs, ratings)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * users.size(0)
            train_mae += torch.abs(outputs - ratings).sum().item()
            
        train_loss /= len(train_loader.dataset)
        train_mae /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_mae = 0.0
        with torch.no_grad():
            for users, movies, ratings in test_loader:
                users, movies, ratings = users.to(device), movies.to(device), ratings.to(device)
                outputs = model(users, movies)
                loss = criterion(outputs, ratings)
                val_loss += loss.item() * users.size(0)
                val_mae += torch.abs(outputs - ratings).sum().item()
                
        val_loss /= len(test_loader.dataset)
        val_mae /= len(test_loader.dataset)
        
        history["loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["mae"].append(train_mae)
        history["val_mae"].append(val_mae)
        
        print(f"Epoch {epoch+1}/{EPOCHS} - loss: {train_loss:.4f} - mae: {train_mae:.4f} - val_loss: {val_loss:.4f} - val_mae: {val_mae:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            torch.save(model.state_dict(), MODEL_PATH)
            patience_counter = 0
            print(f"Saved best model checkpoint to {MODEL_PATH}")
        else:
            praise = "Early stopping check triggered"
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break

    # 5. Save encoders and models
    if progress_callback:
        progress_callback("Finalizing model save & caching encoders…", 90)
        
    save_encoders_after_training(user_enc, movie_enc, n_users, n_movies, movies_df, train_data)

    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
    print(f"[Train] History saved -> {HISTORY_PATH}")

    # Plot metrics
    _plot_history(history)
    
    if progress_callback:
        progress_callback("Training complete! ✅", 100)

    return best_val_loss


def _plot_history(hist: dict):
    """Save history PNG visualization."""
    epochs = range(1, len(hist["loss"]) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("#0d0d0d")
    for ax in (ax1, ax2):
        ax.set_facecolor("#1a1a2e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    # Loss
    ax1.plot(epochs, hist["loss"],     color="#e50914", linewidth=2, label="Train Loss")
    ax1.plot(epochs, hist["val_loss"], color="#f5c518", linewidth=2, linestyle="--", label="Val Loss")
    ax1.set_title("MSE Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend(facecolor="#111", labelcolor="white")

    # MAE
    ax2.plot(epochs, hist["mae"],     color="#00d4aa", linewidth=2, label="Train MAE")
    ax2.plot(epochs, hist["val_mae"], color="#a855f7", linewidth=2, linestyle="--", label="Val MAE")
    ax2.set_title("Mean Absolute Error")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("MAE")
    ax2.legend(facecolor="#111", labelcolor="white")

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Train] Plot saved -> {PLOT_PATH}")
