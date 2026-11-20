"""Regroupe les routes de la version 1 de l'API."""
from fastapi import APIRouter

from app.api.v1.comparisons import router as comparisons_router
from app.api.v1.observations import router as observations_router

router = APIRouter()
router.include_router(observations_router, prefix="/observations", tags=["observations"])
router.include_router(comparisons_router, prefix="/comparisons", tags=["comparisons"])
