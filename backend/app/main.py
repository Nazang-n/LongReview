from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import games, reviews, steam, auth, news, review_tags, favorites, comments, profile, tags
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models to register them with Base.metadata
from app import models

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="LongReview API",
    description="Backend API for LongReview game review platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Start background tasks
from app.services.news_sync import NewsSyncService
from app.services.game_sync import GameSyncService
from app.services.review_scheduler import start_review_scheduler, stop_review_scheduler

@app.on_event("startup")
async def startup_event():
    NewsSyncService.start_scheduler()
    GameSyncService.start_scheduler()
    start_review_scheduler()  # Start daily review update scheduler

@app.on_event("shutdown")
async def shutdown_event():
    NewsSyncService.stop_scheduler()
    GameSyncService.stop_scheduler()
    stop_review_scheduler()  # Stop review scheduler

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(games.router)
app.include_router(reviews.router)
app.include_router(steam.router)
app.include_router(news.router)
app.include_router(review_tags.router)
app.include_router(favorites.router)
app.include_router(comments.router)
app.include_router(profile.router)
app.include_router(tags.router)


@app.get("/", tags=["root"])
def read_root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "Welcome to LongReview API",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
