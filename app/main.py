from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import Base, engine
from app import models  # ensure models registered with SQLAlchemy metadata
from app.routers import users, restaurants, recommendations

app = FastAPI(title="TasteMatch API", version="1.0.0",
              description="Hybrid restaurant recommendations using collaborative filtering, content features, ratings, and location.")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app.mount(
    "/static",
    StaticFiles(directory=str(WEB_DIR)),
    name="static",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list or ["http://localhost:8000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)
app.include_router(users.router, prefix="/api")
app.include_router(restaurants.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/", include_in_schema=False)
def home(): return FileResponse(WEB_DIR / "index.html")

@app.get("/health", tags=["health"])
def health(): return {"status": "ok", "service": "tastematch"}

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/privacy", include_in_schema=False)
def privacy_policy():
    return FileResponse(WEB_DIR / "privacy.html")


@app.get("/terms", include_in_schema=False)
def terms_of_service():
    return FileResponse(WEB_DIR / "terms.html")