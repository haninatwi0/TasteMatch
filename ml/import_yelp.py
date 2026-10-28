"""Import Yelp Open Dataset JSONL files into PostgreSQL.

Download the official dataset manually and place these files in data/:
  yelp_academic_dataset_business.json
  yelp_academic_dataset_review.json
The script streams reviews and only imports reviews for restaurant businesses in the selected city/state.
"""
import argparse, json
from pathlib import Path
from sqlalchemy import select
from app.database import Base, SessionLocal, engine
from app.models import Restaurant, User, Rating

DATA = Path("data")

def parse_price(attributes):
    if not isinstance(attributes, dict): return None
    value = attributes.get("RestaurantsPriceRange2")
    try: return int(value) if value is not None else None
    except (TypeError, ValueError): return None

def is_restaurant(b):
    categories = b.get("categories") or ""
    return "restaurant" in categories.lower() or "food" in categories.lower()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="", help="Optional city filter, e.g. Philadelphia")
    parser.add_argument("--state", default="", help="Optional state filter, e.g. PA")
    parser.add_argument("--max-reviews", type=int, default=250000, help="Limit review rows for manageable local training")
    parser.add_argument("--min-review-stars", type=float, default=1, help="Keep reviews at or above this rating")
    args = parser.parse_args()
    business_file = DATA / "yelp_academic_dataset_business.json"
    review_file = DATA / "yelp_academic_dataset_review.json"
    if not business_file.exists() or not review_file.exists():
        raise SystemExit("Missing Yelp JSON files. See DATASET.md; download the official dataset and place both files in data/.")
    Base.metadata.create_all(engine)
    business_map = {}
    with business_file.open(encoding="utf-8") as fh:
        for line in fh:
            b = json.loads(line)
            if not is_restaurant(b) or b.get("is_open") == 0: continue
            if args.city and b.get("city", "").lower() != args.city.lower(): continue
            if args.state and b.get("state", "").lower() != args.state.lower(): continue
            business_map[b["business_id"]] = b
    if not business_map: raise SystemExit("No matching businesses found. Check the city/state filters and categories.")
    with SessionLocal() as db:
        existing = set(db.scalars(select(Restaurant.id)))
        for bid, b in business_map.items():
            if bid in existing: continue
            db.add(Restaurant(id=bid, name=b.get("name") or "Unnamed restaurant", city=b.get("city") or "",
                state=b.get("state") or "", address=b.get("address") or "", categories=b.get("categories") or "",
                price_level=parse_price(b.get("attributes")), latitude=b.get("latitude"), longitude=b.get("longitude"),
                average_rating=float(b.get("stars") or 0), review_count=int(b.get("review_count") or 0)))
        db.commit()
        # Yelp user IDs are pseudonymous source IDs; map to local integer user IDs.
        user_map = {u.name: u.id for u in db.scalars(select(User).where(User.name.like("yelp:%")))}
        added = 0
        with review_file.open(encoding="utf-8") as fh:
            for line in fh:
                if added >= args.max_reviews: break
                row = json.loads(line)
                if row.get("business_id") not in business_map: continue
                stars = float(row.get("stars") or 0)
                if stars < args.min_review_stars: continue
                source_user = "yelp:" + str(row.get("user_id", ""))
                if not source_user or source_user == "yelp:": continue
                if source_user not in user_map:
                    user = db.scalar(select(User).where(User.name == source_user))
                    if user is None:
                        user = User(name=source_user)
                        db.add(user); db.flush()
                    user_map[source_user] = user.id
                # One rating per user/restaurant for Surprise and the DB uniqueness constraint.
                existing_rating = db.scalar(select(Rating.id).where(Rating.user_id == user_map[source_user], Rating.restaurant_id == row["business_id"]))
                if existing_rating: continue
                db.add(Rating(user_id=user_map[source_user], restaurant_id=row["business_id"], rating=stars))
                added += 1
                if added % 5000 == 0: db.commit(); print(f"Imported {added:,} ratings...")
        db.commit()
    print(f"Imported/retained {len(business_map):,} restaurant businesses and {added:,} ratings.")
    print("Note: Yelp source user identifiers are stored as pseudonymous names for modeling; do not expose them in the UI.")

if __name__ == "__main__": main()
