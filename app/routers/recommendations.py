from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Restaurant, UserInteraction
from app.schemas import RecommendationOut, InteractionCreate
from app.services.recommender import service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/{user_id}", response_model=list[RecommendationOut])
def recommendations(user_id: int, latitude: float | None = Query(None, ge=-90, le=90),
                    longitude: float | None = Query(None, ge=-180, le=180),
                    radius_km: float | None = Query(10, gt=0, le=200),
                    limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return service.recommend(db, user, limit, latitude, longitude, radius_km)

@router.post("/interactions", status_code=201)
def record_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id): raise HTTPException(status_code=404, detail="User not found")
    if not db.get(Restaurant, payload.restaurant_id): raise HTTPException(status_code=404, detail="Restaurant not found")
    db.add(UserInteraction(user_id=payload.user_id, restaurant_id=payload.restaurant_id,
                           interaction_type=payload.interaction_type))
    db.commit()
    return {"message": "Interaction recorded"}
