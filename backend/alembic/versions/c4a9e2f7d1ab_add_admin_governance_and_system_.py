"""add admin governance and system controls

Revision ID: c4a9e2f7d1ab
Revises: 9b3d7f6c2a41
Create Date: 2026-03-19 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a9e2f7d1ab"
down_revision: Union[str, None] = "9b3d7f6c2a41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=32), nullable=True, server_default="user"))
    op.add_column("users", sa.Column("feature_flags", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("suspended_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("suspension_reason", sa.Text(), nullable=True))

    op.add_column("knowledge_bases", sa.Column("category", sa.String(length=128), nullable=True))
    op.add_column("knowledge_bases", sa.Column("department", sa.String(length=128), nullable=True))
    op.add_column("knowledge_bases", sa.Column("sensitivity", sa.String(length=64), nullable=True))
    op.add_column("knowledge_bases", sa.Column("preprocessing_config", sa.JSON(), nullable=True))

    op.add_column("documents", sa.Column("category", sa.String(length=128), nullable=True))
    op.add_column("documents", sa.Column("department", sa.String(length=128), nullable=True))
    op.add_column("documents", sa.Column("sensitivity", sa.String(length=64), nullable=True))
    op.add_column("documents", sa.Column("status", sa.String(length=64), nullable=True, server_default="active"))
    op.add_column("documents", sa.Column("query_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("documents", sa.Column("last_queried_at", sa.DateTime(), nullable=True))
    op.add_column("documents", sa.Column("last_indexed_at", sa.DateTime(), nullable=True))

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)

    op.create_table(
        "access_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_logs_id"), "access_logs", ["id"], unique=False)

    op.create_table(
        "system_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_system_alerts_id"), "system_alerts", ["id"], unique=False)

    op.create_table(
        "system_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_system_configs_id"), "system_configs", ["id"], unique=False)
    op.create_index(op.f("ix_system_configs_key"), "system_configs", ["key"], unique=True)

    op.create_table(
        "manual_qa_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_manual_qa_entries_id"), "manual_qa_entries", ["id"], unique=False)

    op.execute("UPDATE users SET role = 'super_admin' WHERE is_superuser = true")
    op.execute("UPDATE users SET role = 'expert' WHERE role = 'user' AND is_expert = true")
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
    op.execute("UPDATE documents SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE documents SET query_count = 0 WHERE query_count IS NULL")

    op.alter_column("users", "role", existing_type=sa.String(length=32), nullable=False, server_default=None)
    op.alter_column("documents", "status", existing_type=sa.String(length=64), nullable=False, server_default=None)
    op.alter_column("documents", "query_count", existing_type=sa.Integer(), nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_manual_qa_entries_id"), table_name="manual_qa_entries")
    op.drop_table("manual_qa_entries")
    op.drop_index(op.f("ix_system_configs_key"), table_name="system_configs")
    op.drop_index(op.f("ix_system_configs_id"), table_name="system_configs")
    op.drop_table("system_configs")
    op.drop_index(op.f("ix_system_alerts_id"), table_name="system_alerts")
    op.drop_table("system_alerts")
    op.drop_index(op.f("ix_access_logs_id"), table_name="access_logs")
    op.drop_table("access_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_column("documents", "last_indexed_at")
    op.drop_column("documents", "last_queried_at")
    op.drop_column("documents", "query_count")
    op.drop_column("documents", "status")
    op.drop_column("documents", "sensitivity")
    op.drop_column("documents", "department")
    op.drop_column("documents", "category")
    op.drop_column("knowledge_bases", "preprocessing_config")
    op.drop_column("knowledge_bases", "sensitivity")
    op.drop_column("knowledge_bases", "department")
    op.drop_column("knowledge_bases", "category")
    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "suspended_until")
    op.drop_column("users", "feature_flags")
    op.drop_column("users", "role")
