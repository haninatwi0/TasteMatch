from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Restaurant
from app.schemas import RestaurantOut, RatingCreate
from app.models import Rating, User

router = APIRouter(tags=["restaurants"])

@router.get("/restaurants", response_model=list[RestaurantOut])
def list_restaurants(q: str | None = None, city: str | None = None,
                     min_rating: float = Query(0, ge=0, le=5), limit: int = Query(30, ge=1, le=100),
                     db: Session = Depends(get_db)):
    stmt = select(Restaurant).where(Restaurant.average_rating >= min_rating)
    if q: stmt = stmt.where(or_(Restaurant.name.ilike(f"%{q}%"), Restaurant.categories.ilike(f"%{q}%")))
    if city: stmt = stmt.where(Restaurant.city.ilike(f"%{city}%"))
    return list(db.scalars(stmt.order_by(Restaurant.average_rating.desc()).limit(limit)))

@router.get("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def restaurant_detail(restaurant_id: str, db: Session = Depends(get_db)):
    restaurant = db.get(Restaurant, restaurant_id)
    if not restaurant: raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@router.post("/ratings", status_code=201)
def rate_restaurant(payload: RatingCreate, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id): raise HTTPException(status_code=404, detail="User not found")
    if not db.get(Restaurant, payload.restaurant_id): raise HTTPException(status_code=404, detail="Restaurant not found")
    rating = db.scalar(select(Rating).where(Rating.user_id == payload.user_id, Rating.restaurant_id == payload.restaurant_id))
    if rating: rating.rating = payload.rating
    else: db.add(Rating(user_id=payload.user_id, restaurant_id=payload.restaurant_id, rating=payload.rating))
    db.commit()
    return {"message": "Rating saved. Retrain the collaborative model to incorporate it.", "rating": payload.rating}
