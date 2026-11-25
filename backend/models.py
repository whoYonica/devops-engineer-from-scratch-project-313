from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):
    __tablename__ = "links"

    id: int | None = Field(default=None, primary_key=True)
    original_url: str
    short_name: str = Field(unique=True, index=True)

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )