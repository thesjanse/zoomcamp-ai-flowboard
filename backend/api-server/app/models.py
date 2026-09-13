"""Pydantic schemas mirroring ``openapi.yaml``.

Field names use camelCase to match the wire contract exactly. Input schemas
forbid extra properties (``additionalProperties: false`` in the spec) so the
server rejects payloads the frontend contract does not define.
"""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class ErrorResponse(BaseModel):
    title: str | None = None
    detail: str | None = None
    status: int | None = None
    errors: dict[str, list[str]] | None = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthStatus(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Users & auth
# ---------------------------------------------------------------------------

MEMBERSHIP_ROLE = Literal["admin", "member"]
CARD_PRIORITY = Literal["urgent", "high", "medium", "low"]
DUE_FILTER = Literal["all", "overdue", "this-week", "no-date"]
PROJECT_STATUS = Literal["active", "archived"]


class User(BaseModel):
    id: str
    name: str
    email: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8)


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(pattern=EMAIL_PATTERN)
    password: str


class AuthResponse(BaseModel):
    token: str
    user: User


class ChangeEmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(pattern=EMAIL_PATTERN)


class ChangePasswordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentPassword: str
    newPassword: str = Field(min_length=8)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class Member(BaseModel):
    id: str
    name: str
    initials: str
    color: str
    role: MEMBERSHIP_ROLE
    joinedAt: datetime.datetime


class UpdateMemberRoleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: MEMBERSHIP_ROLE


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class Project(BaseModel):
    id: str
    name: str
    key: str
    description: str
    color: str
    icon: str
    status: PROJECT_STATUS
    archived: bool
    creatorId: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    archivedAt: datetime.datetime | None = None
    members: list[Member]


class CreateProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = ""
    color: str | None = None


class UpdateProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    color: str | None = None

    @model_validator(mode="after")
    def not_empty(self) -> "UpdateProjectInput":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class TransferAdminInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adminId: str


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------


class BoardColumn(BaseModel):
    id: str
    projectId: str
    name: str
    color: str
    position: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class CreateColumnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class UpdateColumnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def not_empty(self) -> "UpdateColumnInput":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------


class Card(BaseModel):
    id: str
    projectId: str
    columnId: str
    title: str
    description: str
    priority: CARD_PRIORITY
    assigneeId: str | None = None
    dueDate: datetime.date | None = None
    labels: list[str]
    creatorId: str
    position: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    blockedBy: list[str]
    blocking: list[str]
    commentCount: int


class CardInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    description: str
    priority: CARD_PRIORITY
    assigneeId: str | None = None
    dueDate: datetime.date | None = None
    labels: list[str] = Field(default_factory=list)
    columnId: str


class UpdateCardInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    priority: CARD_PRIORITY | None = None
    assigneeId: str | None = None
    dueDate: datetime.date | None = None
    labels: list[str] | None = None

    @model_validator(mode="after")
    def not_empty(self) -> "UpdateCardInput":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class MoveCardInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columnId: str
    position: int | None = Field(default=None, ge=0)


class DeleteCardInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolveRelationships: Literal["delete", "reconnect"] | None = None
    reconnectToCardId: str | None = None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class Comment(BaseModel):
    id: str
    cardId: str
    authorId: str
    body: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    editedAt: datetime.datetime | None = None


class AddCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1)


class UpdateCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


class Relationship(BaseModel):
    id: str
    sourceCardId: str
    targetCardId: str
    type: Literal["blocks"]
    createdAt: datetime.datetime


class RelationshipSet(BaseModel):
    blockedBy: list[Relationship]
    blocking: list[Relationship]


class CreateRelationshipInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targetCardId: str


# ---------------------------------------------------------------------------
# Board & search
# ---------------------------------------------------------------------------


class BoardSnapshot(BaseModel):
    project: Project
    columns: list[BoardColumn]
    cards: list[Card]
    comments: list[Comment]
    members: list[Member]


class SearchResult(BaseModel):
    type: Literal["project", "card"]
    id: str
    title: str
    subtitle: str


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------


class Invite(BaseModel):
    token: str
    expiresAt: datetime.datetime


class CreateInviteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expiresInDays: int | None = Field(default=None, ge=1)