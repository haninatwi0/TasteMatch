from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    name: str = Field(default="Guest", min_length=1, max_length=120)
    preferred_cuisines: list[str] = []
    dietary_preferences: list[str] = []
    max_price: int | None = Field(default=None, ge=1, le=4)

class UserOut(BaseModel):
    id: int
    name: str
    preferred_cuisines: list[str]
    dietary_preferences: list[str]
    max_price: int | None
    model_config = ConfigDict(from_attributes=True)

class RatingCreate(BaseModel):
    user_id: int
    restaurant_id: str
    rating: float = Field(ge=1, le=5)

class InteractionCreate(BaseModel):
    user_id: int
    restaurant_id: str
    interaction_type: str = Field(default="click", pattern="^(click|save|visit|impression)$")

class RestaurantOut(BaseModel):
    id: str
    name: str
    city: str
    state: str
    address: str
    categories: str
    price_level: int | None
    latitude: float | None
    longitude: float | None
    average_rating: float
    review_count: int
    model_config = ConfigDict(from_attributes=True)

class RecommendationOut(BaseModel):
    restaurant: RestaurantOut
    score: float
    predicted_rating: float | None
    distance_km: float | None
    reason: str
