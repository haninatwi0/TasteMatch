"""Basic held-out rating evaluation for Surprise SVD (RMSE and MAE)."""
import pandas as pd
from sqlalchemy import select
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split
from app.database import SessionLocal
from app.models import Rating

def main():
    with SessionLocal() as db:
        rows = db.execute(select(Rating.user_id, Rating.restaurant_id, Rating.rating)).all()
    if len(rows) < 20: raise SystemExit("Need at least 20 ratings for a simple train/test evaluation.")
    df = pd.DataFrame(rows, columns=["user_id", "restaurant_id", "rating"])
    df["user_id"] = df.user_id.astype(str); df["restaurant_id"] = df.restaurant_id.astype(str)
    data = Dataset.load_from_df(df[["user_id", "restaurant_id", "rating"]], Reader(rating_scale=(1, 5)))
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    algo = SVD(random_state=42)
    algo.fit(trainset)
    predictions = algo.test(testset)
    accuracy.rmse(predictions, verbose=True)
    accuracy.mae(predictions, verbose=True)
    print("This is a random rating split, not a temporal split; use time-based evaluation for stronger claims.")

if __name__ == "__main__": main()
