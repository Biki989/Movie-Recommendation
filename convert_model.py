import os
import pickle
import torch

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "recommender_model.pt")
OUTPUT_PATH = os.path.join(MODEL_DIR, "ncf_weights.pkl")

if not os.path.exists(MODEL_PATH):
    print("Model file not found!")
    exit(1)

state_dict = torch.load(MODEL_PATH, map_location="cpu")
numpy_weights = {}

for key, tensor in state_dict.items():
    numpy_weights[key] = tensor.numpy()
    print(f"Layer {key}: shape {tensor.shape}")

with open(OUTPUT_PATH, "wb") as f:
    pickle.dump(numpy_weights, f)

print(f"Successfully saved numpy weights to {OUTPUT_PATH}")
