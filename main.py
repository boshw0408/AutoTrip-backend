from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from routes import places, hotels, itinerary, trips, ai
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Travel AI Backend starting up...")
    yield
    # Shutdown
    print("👋 Travel AI Backend shutting down...")

app = FastAPI(
    title="Travel AI API",
    description="AI-powered travel planning API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://travel-ai.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
app.include_router(places.router, prefix="/api/places", tags=["places"])
app.include_router(hotels.router, prefix="/api/hotels", tags=["hotels"])
app.include_router(itinerary.router, prefix="/api/itinerary", tags=["itinerary"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/")
async def root():
    return {
        "message": "Travel AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
