from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    parent_dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    version_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ORIGINAL",
        server_default="ORIGINAL",
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PROCESSING",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    analysis: Mapped[
        DatasetAnalysis | None
    ] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        uselist=False,
    )

    parent: Mapped[
        Dataset | None
    ] = relationship(
        "Dataset",
        remote_side="Dataset.id",
        back_populates="versions",
        foreign_keys=[
            parent_dataset_id
        ],
    )

    versions: Mapped[
        list[Dataset]
    ] = relationship(
        "Dataset",
        back_populates="parent",
        foreign_keys=[
            parent_dataset_id
        ],
    )


class DatasetAnalysis(Base):
    __tablename__ = "dataset_analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duplicate_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reliability_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    profile_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    dataset: Mapped[Dataset] = relationship(
        back_populates="analysis",
    )