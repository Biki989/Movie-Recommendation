"""
download_data.py
----------------
Downloads the MovieLens ml-latest-small dataset and extracts
movies.csv and ratings.csv into the data/ directory.

Run once before training:
    python download_data.py
"""

import os
import urllib.request
import zipfile

URL     = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ZIP_PATH = os.path.join(DATA_DIR, "ml-latest-small.zip")

os.makedirs(DATA_DIR, exist_ok=True)

print(f"Downloading MovieLens dataset from:\n  {URL}")
urllib.request.urlretrieve(URL, ZIP_PATH,
    reporthook=lambda b, bs, t: print(f"\r  {min(100, int(b*bs*100/t))}%", end="", flush=True) if t > 0 else None)
print("\nExtracting…")

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    for name in z.namelist():
        if name.endswith("movies.csv") or name.endswith("ratings.csv"):
            # Flatten directory structure → data/movies.csv
            filename = os.path.basename(name)
            with z.open(name) as src, open(os.path.join(DATA_DIR, filename), "wb") as dst:
                dst.write(src.read())
            print(f"  Extracted: {filename}")

os.remove(ZIP_PATH)
print("\nDone! data/movies.csv and data/ratings.csv are ready.")
print("Next step: python train_model.py")
