"""Endpoint de comparaison descriptive de deux périodes historiques."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Observation
from app.schemas import EpisodeComparisonResponse
from app.services.comparison import compare_episodes

router = APIRouter()


@router.get("", response_model=EpisodeComparisonResponse)
def compare_periods(
    first_start_date: date = Query(..., description="Premier mois de la période A (AAAA-MM-01)."),
    first_end_date: date = Query(..., description="Dernier mois de la période A (AAAA-MM-01)."),
    second_start_date: date = Query(..., description="Premier mois de la période B (AAAA-MM-01)."),
    second_end_date: date = Query(..., description="Dernier mois de la période B (AAAA-MM-01)."),
    session: Session = Depends(get_session),
) -> EpisodeComparisonResponse:
    """Compare moyenne et extrêmes ONI sur deux plages mensuelles inclusives."""
    ranges = (
        (first_start_date, first_end_date),
        (second_start_date, second_end_date),
    )
    if any(start > end for start, end in ranges):
        raise HTTPException(status_code=422, detail="Chaque date de début doit précéder ou égaler sa date de fin.")
    if any(boundary.day != 1 for period_range in ranges for boundary in period_range):
        raise HTTPException(status_code=422, detail="Les bornes de comparaison doivent être le premier jour du mois.")

    statement = (
        select(Observation)
        .where(
            or_(
                and_(Observation.period >= first_start_date, Observation.period <= first_end_date),
                and_(Observation.period >= second_start_date, Observation.period <= second_end_date),
            )
        )
        .order_by(Observation.period)
    )
    observations = list(session.scalars(statement).all())
    first_observations = [
        item for item in observations if first_start_date <= item.period <= first_end_date
    ]
    second_observations = [
        item for item in observations if second_start_date <= item.period <= second_end_date
    ]

    if not first_observations or not second_observations:
        raise HTTPException(
            status_code=404,
            detail="Aucune observation ONI ne couvre au moins l'une des périodes demandées.",
        )

    return compare_episodes(first_observations, second_observations)
