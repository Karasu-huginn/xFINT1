"""create expense reports and attachments tables

Revision ID: b3f2a71c9d4e
Revises: 0bd1ec00df00
Create Date: 2026-08-26 21:38:12.407551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f2a71c9d4e"
down_revision: Union[str, None] = "0bd1ec00df00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the expense report and attachment tables with their indexes."""
    op.create_table(
        "expense_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED", "VALIDATED", "REFUSED", "PROCESSED", name="status_enum"
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_expense_reports_owner_id"), "expense_reports", ["owner_id"]
    )
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["report_id"], ["expense_reports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_attachments_report_id"), "attachments", ["report_id"])


def downgrade() -> None:
    """Drop both tables, their indexes and the status enum type."""
    op.drop_index(op.f("ix_attachments_report_id"), table_name="attachments")
    op.drop_table("attachments")
    op.drop_index(op.f("ix_expense_reports_owner_id"), table_name="expense_reports")
    op.drop_table("expense_reports")
    # Autogenerate creates the enum type implicitly with the table but never emits
    # the matching DROP TYPE, so without this line the type survives a downgrade and
    # the next upgrade fails with DuplicateObject. It has to come after the table.
    sa.Enum(name="status_enum").drop(op.get_bind())
