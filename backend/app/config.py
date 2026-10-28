"""Configuration lue depuis les variables d'environnement (ou un fichier .env).

Aucun secret n'est écrit en dur dans le code : tout passe par l'environnement.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://enso:enso@localhost:5432/enso"
    oni_url: str = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    cors_origins: str = "http://localhost:5173"


settings = Settings()
