"""Add dataset registry and link analyses.

Revision ID: 20260730_0002
Revises: 20260730_0001
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260730_0002"
down_revision: str | None = "20260730_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )

    with op.batch_alter_table("dataset_analyses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "dataset_id",
                sa.String(length=36),
                nullable=True,
            )
        )

    connection = op.get_bind()

    existing_analyses = connection.execute(
        sa.text(
            """
            SELECT
                id,
                filename,
                file_size_bytes,
                created_at
            FROM dataset_analyses
            """
        )
    ).mappings()

    for analysis in existing_analyses:
        dataset_id = analysis["id"]

        connection.execute(
            sa.text(
                """
                INSERT INTO datasets (
                    id,
                    original_filename,
                    stored_filename,
                    storage_path,
                    file_size_bytes,
                    status,
                    error_message,
                    uploaded_at,
                    processed_at
                )
                VALUES (
                    :id,
                    :original_filename,
                    :stored_filename,
                    :storage_path,
                    :file_size_bytes,
                    :status,
                    NULL,
                    :uploaded_at,
                    :processed_at
                )
                """
            ),
            {
                "id": dataset_id,
                "original_filename": analysis["filename"],
                "stored_filename": f"legacy-{dataset_id}.csv",
                "storage_path": "",
                "file_size_bytes": analysis["file_size_bytes"],
                "status": "READY",
                "uploaded_at": analysis["created_at"],
                "processed_at": analysis["created_at"],
            },
        )

        connection.execute(
            sa.text(
                """
                UPDATE dataset_analyses
                SET dataset_id = :dataset_id
                WHERE id = :analysis_id
                """
            ),
            {
                "dataset_id": dataset_id,
                "analysis_id": analysis["id"],
            },
        )

    with op.batch_alter_table("dataset_analyses") as batch_op:
        batch_op.alter_column(
            "dataset_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        batch_op.create_index(
            "ix_dataset_analyses_dataset_id",
            ["dataset_id"],
            unique=True,
        )
        batch_op.create_foreign_key(
            "fk_dataset_analyses_dataset_id",
            "datasets",
            ["dataset_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("dataset_analyses") as batch_op:
        batch_op.drop_constraint(
            "fk_dataset_analyses_dataset_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_dataset_analyses_dataset_id",
        )
        batch_op.drop_column(
            "dataset_id",
        )

    op.drop_table("datasets")
    