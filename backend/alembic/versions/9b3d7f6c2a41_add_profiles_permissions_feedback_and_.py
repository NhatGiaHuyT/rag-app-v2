"""add profiles permissions feedback and admin fields

Revision ID: 9b3d7f6c2a41
Revises: 3580c0dcd005
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "9b3d7f6c2a41"
down_revision: Union[str, None] = "3580c0dcd005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("is_expert", sa.Boolean(), nullable=True, server_default=sa.false()))

    op.add_column("knowledge_bases", sa.Column("visibility", sa.String(length=32), nullable=True, server_default="private"))
    op.add_column("documents", sa.Column("access_level", sa.String(length=32), nullable=True, server_default="inherit"))

    op.create_table(
        "knowledge_base_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("knowledge_base_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_level", sa.String(length=32), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("knowledge_base_id", "user_id", name="uq_kb_permission_user"),
    )
    op.create_index(op.f("ix_knowledge_base_permissions_id"), "knowledge_base_permissions", ["id"], unique=False)

    op.create_table(
        "document_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_level", sa.String(length=32), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "user_id", name="uq_document_permission_user"),
    )
    op.create_index(op.f("ix_document_permissions_id"), "document_permissions", ["id"], unique=False)

    op.create_table(
        "message_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_feedback_user"),
    )
    op.create_index(op.f("ix_message_feedback_id"), "message_feedback", ["id"], unique=False)

    op.create_table(
        "message_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("expert_user_id", sa.Integer(), nullable=True),
        sa.Column("content", mysql.LONGTEXT(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["expert_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id"),
    )
    op.create_index(op.f("ix_message_overrides_id"), "message_overrides", ["id"], unique=False)

    op.execute("UPDATE users SET is_expert = false WHERE is_expert IS NULL")
    op.execute("UPDATE knowledge_bases SET visibility = 'private' WHERE visibility IS NULL")
    op.execute("UPDATE documents SET access_level = 'inherit' WHERE access_level IS NULL")

    op.alter_column("users", "is_expert", existing_type=sa.Boolean(), nullable=False, server_default=None)
    op.alter_column("knowledge_bases", "visibility", existing_type=sa.String(length=32), nullable=False, server_default=None)
    op.alter_column("documents", "access_level", existing_type=sa.String(length=32), nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_overrides_id"), table_name="message_overrides")
    op.drop_table("message_overrides")
    op.drop_index(op.f("ix_message_feedback_id"), table_name="message_feedback")
    op.drop_table("message_feedback")
    op.drop_index(op.f("ix_document_permissions_id"), table_name="document_permissions")
    op.drop_table("document_permissions")
    op.drop_index(op.f("ix_knowledge_base_permissions_id"), table_name="knowledge_base_permissions")
    op.drop_table("knowledge_base_permissions")
    op.drop_column("documents", "access_level")
    op.drop_column("knowledge_bases", "visibility")
    op.drop_column("users", "is_expert")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "full_name")
