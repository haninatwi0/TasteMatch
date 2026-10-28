"""Import a Kaggle restaurant-recommendations CSV dataset into PostgreSQL.

Expected files under data/: restaurants.csv, users.csv, ratings.csv (or interactions.csv).
Column names are detected from common aliases. If your dataset uses different names,
run with --help and adapt COLUMN_ALIASES below.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import pandas as pd
from sqlalchemy import select
from app.database import Base, SessionLocal, engine
from app.models import Restaurant, User, Rating

DATA = Path("data")
COLUMN_ALIASES = {
    "restaurant_id": ["restaurant_id", "restaurantid", "item_id", "itemid", "place_id", "id", "business_id"],
    "name": ["name", "restaurant_name", "restaurantname", "title", "restaurant"],
    "cuisine": ["cuisine", "cuisines", "food_type", "category", "categories", "type"],
    "city": ["city", "town", "locality"],
    "state": ["state", "province", "region"],
    "address": ["address", "location", "full_address"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng", "long"],
    "price": ["price_level", "price_tier", "price_range", "price", "cost", "average_cost"],
    "average_rating": ["average_rating", "avg_rating", "rating", "aggregate_rating", "stars", "restaurant_rating"],
    "review_count": ["review_count", "total_reviews", "num_reviews", "votes", "rating_count"],
    "user_id": ["user_id", "userid", "user", "consumer_id", "customer_id"],
    "rating": ["rating", "user_rating", "stars", "score", "overall_rating"],
}

def norm_col(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())

def find_col(df: pd.DataFrame, key: str, required: bool = False) -> str | None:
    lookup = {norm_col(c): c for c in df.columns}
    for alias in COLUMN_ALIASES[key]:
        if norm_col(alias) in lookup:
            return lookup[norm_col(alias)]
    if required:
        raise SystemExit(f"Could not detect required '{key}' column. Available columns: {list(df.columns)}")
    return None

def clean_str(value: object, default: str = "") -> str:
    if pd.isna(value): return default
    return str(value).strip()

def number(value: object) -> float | None:
    if pd.isna(value): return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match: return None
    try: return float(match.group())
    except ValueError: return None

def price_level(value: object) -> int | None:
    if pd.isna(value): return None
    s = str(value).strip()
    if s.count("$") >= 1: return min(4, max(1, s.count("$")))
    n = number(value)
    if n is None: return None
    # Keep 1–4 tier values as tiers; for monetary amounts use coarse relative tiers.
    if n in (1, 2, 3, 4): return int(n)
    return 1 if n < 15 else 2 if n < 35 else 3 if n < 70 else 4

def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists(): raise SystemExit(f"Missing {path}. Download the Kaggle CSV and place it in the data/ folder.")
    try: return pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError: return pd.read_csv(path, encoding="latin-1", low_memory=False)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restaurants", default="restaurants.csv")
    parser.add_argument("--users", default="users.csv")
    parser.add_argument("--ratings", default="ratings.csv", help="Rating/interactions CSV; must include user ID, restaurant ID, and rating")
    parser.add_argument("--max-ratings", type=int, default=200000)
    parser.add_argument("--skip-users-file", action="store_true", help="Use users referenced in ratings even if users.csv is absent")
    args = parser.parse_args()
    restaurant_df = read_csv(DATA / args.restaurants)
    rid_col = find_col(restaurant_df, "restaurant_id", required=True)
    name_col = find_col(restaurant_df, "name")
    cuisine_col = find_col(restaurant_df, "cuisine")
    city_col = find_col(restaurant_df, "city")
    state_col = find_col(restaurant_df, "state")
    address_col = find_col(restaurant_df, "address")
    lat_col = find_col(restaurant_df, "latitude")
    lon_col = find_col(restaurant_df, "longitude")
    price_col = find_col(restaurant_df, "price")
    avg_col = find_col(restaurant_df, "average_rating")
    count_col = find_col(restaurant_df, "review_count")
    if not args.skip_users_file and (DATA / args.users).exists():
        users_df = read_csv(DATA / args.users)
        user_source_col = find_col(users_df, "user_id", required=True)
        user_name_col = find_col(users_df, "name")
    else:
        users_df = pd.DataFrame()
        user_source_col = user_name_col = None
    ratings_path = DATA / args.ratings
    if not ratings_path.exists() and args.ratings == "ratings.csv" and (DATA / "interactions.csv").exists():
        ratings_path = DATA / "interactions.csv"
    ratings_df = read_csv(ratings_path)
    rating_user_col = find_col(ratings_df, "user_id", required=True)
    rating_rest_col = find_col(ratings_df, "restaurant_id", required=True)
    rating_value_col = find_col(ratings_df, "rating", required=True)

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        known_restaurants = set(db.scalars(select(Restaurant.id)))
        restaurant_rows = 0
        for _, row in restaurant_df.iterrows():
            source_id = clean_str(row[rid_col])
            if not source_id or source_id.lower() == "nan" or source_id in known_restaurants: continue
            name = clean_str(row[name_col], f"Restaurant {source_id}") if name_col else f"Restaurant {source_id}"
            cuisine = clean_str(row[cuisine_col]) if cuisine_col else ""
            city = clean_str(row[city_col]) if city_col else ""
            state = clean_str(row[state_col]) if state_col else ""
            address = clean_str(row[address_col]) if address_col else ""
            lat, lon = (number(row[lat_col]) if lat_col else None), (number(row[lon_col]) if lon_col else None)
            avg = number(row[avg_col]) if avg_col else None
            reviews = number(row[count_col]) if count_col else 0
            db.add(Restaurant(id=source_id, name=name, city=city, state=state, address=address,
                categories=cuisine, price_level=price_level(row[price_col]) if price_col else None,
                latitude=lat, longitude=lon, average_rating=min(5, max(0, avg or 0)),
                review_count=max(0, int(reviews or 0))))
            known_restaurants.add(source_id); restaurant_rows += 1
        db.commit()

        source_user_names: dict[str, str] = {}
        if not users_df.empty and user_source_col:
            for _, row in users_df.iterrows():
                source_id = clean_str(row[user_source_col])
                if source_id and source_id.lower() != "nan":
                    source_user_names[source_id] = clean_str(row[user_name_col], f"Dataset user {source_id}") if user_name_col else f"Dataset user {source_id}"
        # Load existing mappings and create local users for source user IDs.
        user_map = {u.name.removeprefix("dataset:"): u.id for u in db.scalars(select(User).where(User.name.like("dataset:%")))}
        restaurant_ids = set(db.scalars(select(Restaurant.id)))
        added_ratings = 0
        ratings_df = ratings_df.head(args.max_ratings)
        # Deduplicate source interactions to the latest row per user/restaurant if timestamps are available.
        ratings_df = ratings_df.drop_duplicates(subset=[rating_user_col, rating_rest_col], keep="last")
        for _, row in ratings_df.iterrows():
            source_user = clean_str(row[rating_user_col]); source_rest = clean_str(row[rating_rest_col])
            value = number(row[rating_value_col])
            if not source_user or source_user.lower() == "nan" or source_rest not in restaurant_ids or value is None: continue
            # Surprise expects ratings on a 1–5 scale; ignore invalid values.
            if value < 1 or value > 5: continue
            if source_user not in user_map:
                user = User(name="dataset:" + source_user)
                db.add(user); db.flush(); user_map[source_user] = user.id
            existing = db.scalar(select(Rating).where(Rating.user_id == user_map[source_user], Rating.restaurant_id == source_rest))
            if existing:
                existing.rating = float(value)
            else:
                db.add(Rating(user_id=user_map[source_user], restaurant_id=source_rest, rating=float(value)))
            added_ratings += 1
            if added_ratings % 5000 == 0: db.commit(); print(f"Processed {added_ratings:,} ratings...")
        db.commit()
    print(f"Imported {restaurant_rows:,} new restaurants and processed {added_ratings:,} ratings.")
    print("Next: python -m ml.evaluate, then python -m ml.train")

if __name__ == "__main__": main()
