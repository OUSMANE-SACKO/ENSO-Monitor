"""Application FastAPI ENSO Monitor."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import settings

app = FastAPI(
    title="ENSO Monitor API",
    description="Consultation des observations historiques de l'indice NOAA ONI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
