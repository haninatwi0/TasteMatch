from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])

def split_csv(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]

@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, preferred_cuisines=", ".join(payload.preferred_cuisines),
                dietary_preferences=", ".join(payload.dietary_preferences), max_price=payload.max_price)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "preferred_cuisines": split_csv(user.preferred_cuisines),
            "dietary_preferences": split_csv(user.dietary_preferences), "max_price": user.max_price}

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "preferred_cuisines": split_csv(user.preferred_cuisines),
            "dietary_preferences": split_csv(user.dietary_preferences), "max_price": user.max_price}
