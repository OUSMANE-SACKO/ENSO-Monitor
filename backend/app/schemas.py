"""Schémas de réponse de l'API."""
from datetime import date

from pydantic import BaseModel, ConfigDict


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: date
    season: str
    total: float
    anomaly: float


class EpisodeSummary(BaseModel):
    start_date: date
    end_date: date
    observation_count: int
    mean_anomaly: float
    maximum_anomaly: float
    maximum_period: date
    minimum_anomaly: float
    minimum_period: date


class EpisodeComparisonResponse(BaseModel):
    first: EpisodeSummary
    second: EpisodeSummary
    mean_anomaly_difference: float
    interpretation: str
    caveats: list[str]
