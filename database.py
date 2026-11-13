import os
from functools import lru_cache

from sqlmodel import create_engine

from models import Link


@lru_cache
def get_engine():
    database_url = os.environ["DATABASE_URL"]

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return create_engine(database_url, pool_pre_ping=True)


def create_db_and_tables():
    engine = get_engine()
    Link.metadata.create_all(engine)