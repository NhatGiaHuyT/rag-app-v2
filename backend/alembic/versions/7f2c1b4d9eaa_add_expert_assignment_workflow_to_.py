"""add expert assignment workflow to feedback

Revision ID: 7f2c1b4d9eaa
Revises: c4a9e2f7d1ab
Create Date: 2026-03-19 01:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f2c1b4d9eaa"
down_revision: Union[str, None] = "c4a9e2f7d1ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("message_feedback", sa.Column("status", sa.String(length=32), nullable=True, server_default="submitted"))
    op.add_column("message_feedback", sa.Column("expert_assignee_id", sa.Integer(), nullable=True))
    op.add_column("message_feedback", sa.Column("assignment_note", sa.Text(), nullable=True))
    op.add_column("message_feedback", sa.Column("assigned_at", sa.DateTime(), nullable=True))
    op.add_column("message_feedback", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_message_feedback_expert_assignee",
        "message_feedback",
        "users",
        ["expert_assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute("UPDATE message_feedback SET status = 'flagged' WHERE rating = 'down'")
    op.execute("UPDATE message_feedback SET status = 'submitted' WHERE status IS NULL")
    op.alter_column("message_feedback", "status", existing_type=sa.String(length=32), nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_message_feedback_expert_assignee", "message_feedback", type_="foreignkey")
    op.drop_column("message_feedback", "resolved_at")
    op.drop_column("message_feedback", "assigned_at")
    op.drop_column("message_feedback", "assignment_note")
    op.drop_column("message_feedback", "expert_assignee_id")
    op.drop_column("message_feedback", "status")
