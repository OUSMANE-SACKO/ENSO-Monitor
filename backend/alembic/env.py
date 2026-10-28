"""Alembic : applique les migrations sur la base définie par DATABASE_URL."""
from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401  (enregistre les tables dans Base.metadata)
from app.config import settings
from app.db import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = context.config.attributes.get("database_url", settings.database_url)
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
