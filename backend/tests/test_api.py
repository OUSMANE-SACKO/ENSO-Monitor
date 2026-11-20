"""Tests de l'API de consultation sans dépendance à un serveur PostgreSQL."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app


def observation(period: date, season: str, total: float, anomaly: float) -> SimpleNamespace:
    return SimpleNamespace(period=period, season=season, total=total, anomaly=anomaly)


def test_observations_retournees_dans_un_format_stable():
    fake_session = Mock()
    fake_session.scalars.return_value.all.return_value = [
        observation(date(2000, 1, 1), "DJF", 25.4, -1.7)
    ]
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get("/api/v1/observations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "period": "2000-01-01",
            "season": "DJF",
            "total": 25.4,
            "anomaly": -1.7,
        }
    ]


def test_dates_inversees_sont_refusees_sans_interroger_la_base():
    fake_session = Mock()
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get(
            "/api/v1/observations",
            params={"start_date": "2000-03-01", "end_date": "2000-01-01"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "start_date doit être antérieure ou égale à end_date."
    fake_session.scalars.assert_not_called()


def test_filtres_de_dates_sont_appliques_a_la_requete():
    fake_session = Mock()
    fake_session.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get(
            "/api/v1/observations",
            params={"start_date": "2000-01-01", "end_date": "2000-12-01"},
        )
    finally:
        app.dependency_overrides.clear()

    statement = fake_session.scalars.call_args.args[0]
    compiled = statement.compile()

    assert response.status_code == 200
    assert "observation.period >= " in str(compiled)
    assert "observation.period <= " in str(compiled)
    assert set(compiled.params.values()) == {date(2000, 1, 1), date(2000, 12, 1)}


def test_format_de_date_invalide_est_refuse():
    response = TestClient(app).get(
        "/api/v1/observations",
        params={"start_date": "pas-une-date"},
    )

    assert response.status_code == 422


def test_comparaison_retourne_mesures_et_limites():
    fake_session = Mock()
    fake_session.scalars.return_value.all.return_value = [
        observation(date(1997, 1, 1), "DJF", 26.4, 0.4),
        observation(date(1997, 2, 1), "JFM", 27.1, 1.1),
        observation(date(2010, 1, 1), "DJF", 24.7, -1.3),
        observation(date(2010, 2, 1), "JFM", 24.2, -1.8),
    ]
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get(
            "/api/v1/comparisons",
            params={
                "first_start_date": "1997-01-01",
                "first_end_date": "1997-02-01",
                "second_start_date": "2010-01-01",
                "second_end_date": "2010-02-01",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    result = response.json()
    assert result["first"]["observation_count"] == 2
    assert result["first"]["mean_anomaly"] == 0.75
    assert result["second"]["mean_anomaly"] == -1.55
    assert result["mean_anomaly_difference"] == 2.3
    assert "supérieure de 2,30 °C" in result["interpretation"]
    assert any("pas classées automatiquement" in caveat for caveat in result["caveats"])


def test_comparaison_bornes_inversees_refusees():
    fake_session = Mock()
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get(
            "/api/v1/comparisons",
            params={
                "first_start_date": "1997-03-01",
                "first_end_date": "1997-02-01",
                "second_start_date": "2010-01-01",
                "second_end_date": "2010-02-01",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    fake_session.scalars.assert_not_called()


def test_comparaison_sans_observation_retourne_404():
    fake_session = Mock()
    fake_session.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_session] = lambda: fake_session

    try:
        response = TestClient(app).get(
            "/api/v1/comparisons",
            params={
                "first_start_date": "1997-01-01",
                "first_end_date": "1997-02-01",
                "second_start_date": "2010-01-01",
                "second_end_date": "2010-02-01",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
