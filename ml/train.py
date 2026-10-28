"""Train Surprise SVD and scikit-learn TF-IDF content model from PostgreSQL."""
from pathlib import Path
import joblib
import pandas as pd
from sqlalchemy import select
from surprise import Dataset, Reader, SVD
from app.database import SessionLocal
from app.models import Rating, Restaurant
from sklearn.feature_extraction.text import TfidfVectorizer

OUT = Path("ml/artifacts")
OUT.mkdir(parents=True, exist_ok=True)

def main():
    with SessionLocal() as db:
        rating_rows = db.execute(select(Rating.user_id, Rating.restaurant_id, Rating.rating)).all()
        restaurants = list(db.scalars(select(Restaurant)))
    if len(rating_rows) < 10: raise SystemExit("Not enough ratings. Import Yelp reviews first (recommended: at least hundreds).")
    ratings = pd.DataFrame(rating_rows, columns=["user_id", "restaurant_id", "rating"])
    ratings["user_id"] = ratings["user_id"].astype(str)
    ratings["restaurant_id"] = ratings["restaurant_id"].astype(str)
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[["user_id", "restaurant_id", "rating"]], reader)
    trainset = data.build_full_trainset()
    model = SVD(n_factors=50, n_epochs=20, random_state=42)
    model.fit(trainset)
    joblib.dump(model, OUT / "collaborative.joblib")
    restaurant_ids, texts = [], []
    for r in restaurants:
        restaurant_ids.append(r.id)
        texts.append(f"{r.name} {r.categories} {r.city} {r.state} price_{r.price_level or 'unknown'}")
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(texts)
    joblib.dump({"vectorizer": vectorizer, "matrix": matrix, "restaurant_ids": restaurant_ids}, OUT / "content.joblib")
    print(f"Saved models to {OUT.resolve()}. Restaurants={len(restaurants):,}; ratings={len(ratings):,}.")
    print("This script trains on all available ratings for serving. For formal evaluation, use ml/evaluate.py with a held-out test split.")

if __name__ == "__main__": main()
