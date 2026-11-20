"""Calculs descriptifs pour comparer deux périodes ONI choisies."""
from dataclasses import dataclass
from typing import Sequence

from app.models import Observation
from app.schemas import EpisodeComparisonResponse, EpisodeSummary


@dataclass(frozen=True)
class EpisodeStatistics:
    summary: EpisodeSummary
    mean_anomaly: float


def format_celsius(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def summarize_episode(observations: Sequence[Observation]) -> EpisodeStatistics:
    if not observations:
        raise ValueError("Impossible de résumer une période sans observation.")

    ordered = sorted(observations, key=lambda observation: observation.period)
    anomalies = [float(observation.anomaly) for observation in ordered]
    maximum_index = max(range(len(ordered)), key=anomalies.__getitem__)
    minimum_index = min(range(len(ordered)), key=anomalies.__getitem__)
    mean_anomaly = sum(anomalies) / len(anomalies)

    return EpisodeStatistics(
        summary=EpisodeSummary(
            start_date=ordered[0].period,
            end_date=ordered[-1].period,
            observation_count=len(ordered),
            mean_anomaly=round(mean_anomaly, 2),
            maximum_anomaly=round(anomalies[maximum_index], 2),
            maximum_period=ordered[maximum_index].period,
            minimum_anomaly=round(anomalies[minimum_index], 2),
            minimum_period=ordered[minimum_index].period,
        ),
        mean_anomaly=mean_anomaly,
    )


def compare_episodes(
    first_observations: Sequence[Observation],
    second_observations: Sequence[Observation],
) -> EpisodeComparisonResponse:
    first = summarize_episode(first_observations)
    second = summarize_episode(second_observations)
    difference = first.mean_anomaly - second.mean_anomaly
    magnitude = abs(difference)

    if magnitude < 0.005:
        interpretation = (
            "Les anomalies ONI moyennes des deux périodes sont très proches "
            f"(écart arrondi à {format_celsius(magnitude)} °C)."
        )
    elif difference > 0:
        interpretation = (
            f"La période A présente une anomalie ONI moyenne supérieure de "
            f"{format_celsius(magnitude)} °C à celle de la période B."
        )
    else:
        interpretation = (
            f"La période B présente une anomalie ONI moyenne supérieure de "
            f"{format_celsius(magnitude)} °C à celle de la période A."
        )

    return EpisodeComparisonResponse(
        first=first.summary,
        second=second.summary,
        mean_anomaly_difference=round(difference, 2),
        interpretation=interpretation,
        caveats=[
            "La comparaison porte uniquement sur les observations ONI disponibles; les mois manquants ne sont pas interpolés.",
            "Des périodes de durées différentes ne sont pas strictement équivalentes; le nombre de mesures est affiché.",
            "Les périodes ne sont pas classées automatiquement comme El Niño ou La Niña.",
            "L'ONI est une moyenne glissante sur trois mois; moyenne et extrêmes ne décrivent pas seuls les impacts régionaux, les causes ou les prévisions.",
        ],
    )
