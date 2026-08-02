"""Add dataset versioning fields.

Revision ID: 20260801_0002
Revises: 20260730_0002
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_0002"
down_revision: str | None = "20260730_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table(
        "datasets",
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "parent_dataset_id",
                sa.String(length=36),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "version_number",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )

        batch_op.add_column(
            sa.Column(
                "version_type",
                sa.String(length=20),
                nullable=False,
                server_default="ORIGINAL",
            )
        )

        batch_op.create_foreign_key(
            "fk_datasets_parent_dataset_id",
            "datasets",
            [
                "parent_dataset_id",
            ],
            [
                "id",
            ],
            ondelete="SET NULL",
        )

        batch_op.create_index(
            "ix_datasets_parent_dataset_id",
            [
                "parent_dataset_id",
            ],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "datasets",
    ) as batch_op:
        batch_op.drop_index(
            "ix_datasets_parent_dataset_id"
        )

        batch_op.drop_constraint(
            "fk_datasets_parent_dataset_id",
            type_="foreignkey",
        )

        batch_op.drop_column(
            "version_type"
        )

        batch_op.drop_column(
            "version_number"
        )

        batch_op.drop_column(
            "parent_dataset_id"
        )