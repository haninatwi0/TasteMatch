
import csv
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Restaurant


PROJECT_DIR = Path(__file__).resolve().parent
CSV_PATH = PROJECT_DIR / "data" / "restaurants.csv"

PRICE_LEVELS = {
    "$": 1,
    "$$": 2,
    "$$$": 3,
    "$$$$": 4,
}


def import_restaurants() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Restaurant CSV not found: {CSV_PATH}"
        )

    Base.metadata.create_all(bind=engine)

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        required_columns = {
            "restaurant_id",
            "name",
            "cuisine",
            "rating",
            "price_range",
            "location",
        }

        actual_columns = set(reader.fieldnames or [])
        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ValueError(
                f"Missing CSV columns: {sorted(missing_columns)}"
            )

        imported_count = 0
        seen_ids = set()

        with SessionLocal() as db:
            try:
                for row in reader:
                    restaurant_id = (
                        row["restaurant_id"] or ""
                    ).strip()

                    if not restaurant_id:
                        continue

                    if restaurant_id in seen_ids:
                        continue

                    seen_ids.add(restaurant_id)

                    name = (row["name"] or "").strip()
                    cuisine = (row["cuisine"] or "").strip()
                    location = (row["location"] or "").strip()
                    price_text = (
                        row["price_range"] or ""
                    ).strip()

                    if not name:
                        continue

                    try:
                        rating = float(row["rating"])
                    except (TypeError, ValueError):
                        rating = 0.0

                    rating = max(0.0, min(5.0, rating))
                    price_level = PRICE_LEVELS.get(price_text)

                    restaurant = Restaurant(
                        id=restaurant_id,
                        name=name,
                        city=location,
                        state="",
                        address="",
                        categories=cuisine,
                        price_level=price_level,
                        latitude=None,
                        longitude=None,
                        average_rating=rating,
                        review_count=0,
                    )

                    # Insert new records or update existing ones.
                    db.merge(restaurant)
                    imported_count += 1

                db.commit()

                total = db.scalar(
                    select(Restaurant.id)
                )

                print(
                    f"Import complete. Processed "
                    f"{imported_count} unique restaurant records."
                )
                print(
                    "The transaction was committed successfully."
                )

            except Exception:
                db.rollback()
                raise


if __name__ == "__main__":
    import_restaurants()