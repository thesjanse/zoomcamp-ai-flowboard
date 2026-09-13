"""SQLAlchemy ORM models for the data layer.

Fields mirror the store entities from the original in-memory implementation.
CamelCase keys used by the API are derived in the store layer; here we use
snake_case columns that map cleanly to any SQL database.
"""

from __future__ import annotations

import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, TZDateTime


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    initials: Mapped[str] = mapped_column(String(8))
    color: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(16))
    icon: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default="active")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    creator_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    archived_at: Mapped[datetime.datetime | None] = mapped_column(TZDateTime, nullable=True)
    next_card_number: Mapped[int] = mapped_column(Integer, default=1)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16), default="member")
    joined_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(16))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    column_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    assignee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    labels: Mapped[list] = mapped_column(JSON, default=list)
    creator_id: Mapped[str] = mapped_column(String(64))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    card_id: Mapped[str] = mapped_column(String(64), index=True)
    author_id: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    edited_at: Mapped[datetime.datetime | None] = mapped_column(TZDateTime, nullable=True)


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (UniqueConstraint("source_card_id", "target_card_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_card_id: Mapped[str] = mapped_column(String(64), index=True)
    target_card_id: Mapped[str] = mapped_column(String(64), index=True)
    type: Mapped[str] = mapped_column(String(16), default="blocks")
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class Invite(Base):
    __tablename__ = "invites"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    created_by: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(TZDateTime)


class Counter(Base):
    __tablename__ = "counters"

    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, default=1)