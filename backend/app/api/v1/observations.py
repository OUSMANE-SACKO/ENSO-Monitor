"""Endpoints de consultation des observations ONI."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Observation
from app.schemas import ObservationResponse

router = APIRouter()


@router.get("", response_model=list[ObservationResponse])
def list_observations(
    start_date: date | None = Query(default=None, description="Première période incluse (AAAA-MM-JJ)."),
    end_date: date | None = Query(default=None, description="Dernière période incluse (AAAA-MM-JJ)."),
    session: Session = Depends(get_session),
) -> list[Observation]:
    """Retourne les observations classées chronologiquement, bornes incluses."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date doit être antérieure ou égale à end_date.",
        )

    statement = select(Observation).order_by(Observation.period)
    if start_date is not None:
        statement = statement.where(Observation.period >= start_date)
    if end_date is not None:
        statement = statement.where(Observation.period <= end_date)

    return list(session.scalars(statement).all())
