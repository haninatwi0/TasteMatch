"""Hybrid recommendation logic; ML artifacts are optional until trained."""
from __future__ import annotations
import math
from pathlib import Path
import joblib
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Rating, Restaurant, User

MODEL_PATH = Path(settings.model_dir)

class RecommendationService:
    def __init__(self) -> None:
        self.svd = None
        self.vectorizer = None
        self.content_matrix = None
        self.restaurant_ids: list[str] = []
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        try:
            path = MODEL_PATH / "collaborative.joblib"
            if path.exists(): self.svd = joblib.load(path)
            content_path = MODEL_PATH / "content.joblib"
            if content_path.exists():
                artifact = joblib.load(content_path)
                self.vectorizer = artifact["vectorizer"]
                self.content_matrix = artifact["matrix"]
                self.restaurant_ids = artifact["restaurant_ids"]
        except (OSError, ValueError, KeyError):
            # API stays usable with popularity/content fallback if artifacts are absent.
            self.svd = self.vectorizer = self.content_matrix = None

    @staticmethod
    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 2 * radius * math.asin(math.sqrt(min(1.0, a)))

    @staticmethod
    def _quality(r: Restaurant) -> float:
        # Bayesian shrinkage avoids over-ranking businesses with only one review.
        global_mean, prior_reviews = 3.7, 20
        return ((r.review_count / (r.review_count + prior_reviews)) * r.average_rating
                + (prior_reviews / (r.review_count + prior_reviews)) * global_mean) / 5.0

    @staticmethod
    def _tokens(user: User) -> set[str]:
        raw = f"{user.preferred_cuisines or ''},{user.dietary_preferences or ''}"
        return {x.strip().lower() for x in raw.split(",") if x.strip()}

    def _content_score(self, restaurant: Restaurant, user: User) -> float:
        tokens = self._tokens(user)
        if self.vectorizer is not None and self.content_matrix is not None and restaurant.id in self.restaurant_ids:
            # Use a user preference text query against the restaurant TF-IDF vectors.
            query = " ".join([*tokens, str(user.max_price or "")])
            if query.strip():
                qvec = self.vectorizer.transform([query])
                idx = self.restaurant_ids.index(restaurant.id)
                from sklearn.metrics.pairwise import cosine_similarity
                return float(cosine_similarity(qvec, self.content_matrix[idx])[0, 0])
        categories = {x.strip().lower() for x in (restaurant.categories or "").replace(";", ",").split(",") if x.strip()}
        if not tokens:
            return 0.5
        matched = sum(1 for token in tokens if any(token in category or category in token for category in categories))
        return matched / len(tokens)

    def recommend(self, db: Session, user: User, limit: int = 10, latitude: float | None = None,
                  longitude: float | None = None, radius_km: float | None = 10.0) -> list[dict]:
        restaurants = list(db.scalars(select(Restaurant)))
        rated_ids = set(db.scalars(select(Rating.restaurant_id).where(Rating.user_id == user.id)))
        output = []
        for r in restaurants:
            if r.id in rated_ids: continue
            if user.max_price and r.price_level and r.price_level > user.max_price: continue
            distance = None
            if latitude is not None and longitude is not None and r.latitude is not None and r.longitude is not None:
                distance = self.distance_km(latitude, longitude, r.latitude, r.longitude)
                if radius_km is not None and distance > radius_km: continue
            cf = None
            if self.svd is not None:
                # Surprise returns a global-mean estimate for unknown IDs. Only call it
                # collaborative evidence when BOTH user and restaurant were in training.
                known_users = getattr(getattr(self.svd, "trainset", None), "_raw2inner_id_users", {})
                known_items = getattr(getattr(self.svd, "trainset", None), "_raw2inner_id_items", {})
                if str(user.id) in known_users and r.id in known_items:
                    try: cf = float(self.svd.predict(str(user.id), r.id).est)
                    except (ValueError, KeyError, AttributeError): cf = None
            content = self._content_score(r, user)
            quality = self._quality(r)
            proximity = math.exp(-distance / 5.0) if distance is not None else 0.5
            if cf is not None:
                cf_norm = min(1.0, max(0.0, (cf - 1.0) / 4.0))
                score = 0.45*cf_norm + 0.30*content + 0.15*quality + 0.10*proximity
                predicted = round(cf, 2)
            else:
                # Cold-start fallback when a collaborative model/user mapping is unavailable.
                score = 0.50*content + 0.30*quality + 0.20*proximity
                predicted = None
            if content >= 0.25 and self._tokens(user): reason = "Matches your cuisine or dietary preferences"
            elif distance is not None and distance < 3: reason = "Highly rated and close to your location"
            else: reason = "Recommended from restaurant quality and available preference signals"
            output.append({"restaurant": r, "score": round(float(score), 4), "predicted_rating": predicted,
                           "distance_km": round(distance, 2) if distance is not None else None, "reason": reason})
        output.sort(key=lambda x: x["score"], reverse=True)
        return output[:limit]

service = RecommendationService()
