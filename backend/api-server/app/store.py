"""SQLAlchemy-backed data store and seed data.

The ``Store`` is the single data-access layer for the API.  Every method
mirrors the shape of the original in-memory store: entities are returned as
plain dicts with camelCase keys, so routers and serialization stay unchanged.
Each method opens its own short-lived session and commits on success.

The store is database-agnostic: it only uses the SQLAlchemy engine given to
it (defaults to ``config.DATABASE_URL``), so swapping SQLite for Postgres is
just a matter of changing the connection URL.
"""

from __future__ import annotations

import datetime
import hashlib
import re
import secrets
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .auth import hash_password
from .database import get_engine, init_db
from .orm import (
    BoardColumn,
    Card,
    Comment,
    Counter,
    Invite,
    Membership,
    Project,
    Relationship,
    User,
)

UTC = datetime.timezone.utc

DEFAULT_COLUMN_COLOR = "#8e96a3"
PALETTE = [
    "#db805e",
    "#5f8f77",
    "#7a72ad",
    "#c58b42",
    "#8e96a3",
    "#4d7ea8",
    "#a85f7a",
    "#5e8a6b",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(UTC)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if len(parts) == 0:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def derive_key(name: str) -> str:
    words = [w for w in re.split(r"\W+", name) if w]
    key = "".join(w[0] for w in words[:3]).upper()
    return key or name[:3].upper()


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class Store:
    def __init__(self, engine=None, *, seed: bool = True) -> None:
        self.engine = engine or get_engine()
        init_db(self.engine)
        if seed:
            self.seed()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def _session(self) -> Session:
        return Session(bind=self.engine)

    # ------------------------------------------------------------------
    # Row -> dict serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _user_row(row: User) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "initials": row.initials,
            "color": row.color,
            "passwordHash": row.password_hash,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
        }

    @staticmethod
    def _project_row(row: Project) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "key": row.key,
            "description": row.description,
            "color": row.color,
            "icon": row.icon,
            "status": row.status,
            "archived": row.archived,
            "creatorId": row.creator_id,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
            "archivedAt": row.archived_at,
            "nextCardNumber": row.next_card_number,
        }

    @staticmethod
    def _column_row(row: BoardColumn) -> dict:
        return {
            "id": row.id,
            "projectId": row.project_id,
            "name": row.name,
            "color": row.color,
            "position": row.position,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
        }

    @staticmethod
    def _card_row(row: Card) -> dict:
        return {
            "id": row.id,
            "projectId": row.project_id,
            "columnId": row.column_id,
            "title": row.title,
            "description": row.description,
            "priority": row.priority,
            "assigneeId": row.assignee_id,
            "dueDate": row.due_date,
            "labels": list(row.labels or []),
            "creatorId": row.creator_id,
            "position": row.position,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
        }

    @staticmethod
    def _comment_row(row: Comment) -> dict:
        return {
            "id": row.id,
            "cardId": row.card_id,
            "authorId": row.author_id,
            "body": row.body,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
            "editedAt": row.edited_at,
        }

    @staticmethod
    def _rel_row(row: Relationship) -> dict:
        return {
            "id": row.id,
            "sourceCardId": row.source_card_id,
            "targetCardId": row.target_card_id,
            "type": row.type,
            "createdAt": row.created_at,
        }

    def _member_dict(self, user_row: User, membership: Membership) -> dict:
        return {
            "id": user_row.id,
            "name": user_row.name,
            "initials": user_row.initials,
            "color": user_row.color,
            "role": membership.role,
            "joinedAt": membership.joined_at,
        }

    # ------------------------------------------------------------------
    # ID helpers
    # ------------------------------------------------------------------

    def _next_id(self, session: Session, kind: str) -> str:
        row = session.get(Counter, kind)
        if row is None:
            row = Counter(name=kind, next_value=1)
            session.add(row)
            value = 1
        else:
            value = row.next_value
        row.next_value = value + 1
        return f"{kind}-{value}"

    def _set_counter(self, session: Session, kind: str, value: int) -> None:
        row = session.get(Counter, kind)
        if row is None:
            session.add(Counter(name=kind, next_value=value + 1))
        else:
            row.next_value = value + 1

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_user(self, user_id: str | None) -> dict | None:
        if user_id is None:
            return None
        with self._session() as session:
            row = session.get(User, user_id)
            return self._user_row(row) if row else None

    def get_user_by_email(self, email: str) -> dict | None:
        with self._session() as session:
            row = session.execute(
                select(User).where(User.email == email.lower())
            ).scalar_one_or_none()
            return self._user_row(row) if row else None

    def _insert_user(
        self,
        session: Session,
        uid: str,
        name: str,
        email: str,
        password: str,
        color: str,
    ) -> dict:
        now = utcnow()
        user = User(
            id=uid,
            name=name,
            email=email.lower(),
            initials=compute_initials(name),
            color=color,
            password_hash=hash_password(password),
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        return self._user_row(user)

    def create_user(self, name: str, email: str, password_hash: str) -> dict:
        now = utcnow()
        with self._session() as session:
            user = User(
                id=self._next_id(session, "user"),
                name=name,
                email=email.lower(),
                initials=compute_initials(name),
                color=PALETTE[hash(name) % len(PALETTE)],
                password_hash=password_hash,
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            session.commit()
            return self._user_row(user)

    def update_user_email(self, user: dict, email: str) -> dict:
        with self._session() as session:
            row = session.get(User, user["id"])
            row.email = email.lower()
            row.updated_at = utcnow()
            session.commit()
            return self._user_row(row)

    def update_user_password(self, user: dict, password_hash: str) -> dict:
        with self._session() as session:
            row = session.get(User, user["id"])
            row.password_hash = password_hash
            row.updated_at = utcnow()
            session.commit()
            return self._user_row(row)

    def user_to_dict(self, user: dict) -> dict:
        return {k: user[k] for k in ("id", "name", "email", "createdAt", "updatedAt")}

    def user_display_name(self, user_id: str | None) -> str:
        user = self.get_user(user_id)
        return user["name"] if user else "Deleted user"

    # ------------------------------------------------------------------
    # Memberships
    # ------------------------------------------------------------------

    def add_member(
        self, project: dict, user: dict, role: str = "member", *, joined_at: datetime.datetime | None = None
    ) -> None:
        with self._session() as session:
            session.add(
                Membership(
                    project_id=project["id"],
                    user_id=user["id"],
                    role=role,
                    joined_at=joined_at or utcnow(),
                )
            )
            session.commit()

    def remove_member(self, project: dict, user: dict) -> None:
        with self._session() as session:
            session.execute(
                delete(Membership).where(
                    Membership.project_id == project["id"],
                    Membership.user_id == user["id"],
                )
            )
            session.commit()

    def get_membership(self, project_id: str, user_id: str) -> dict | None:
        with self._session() as session:
            row = session.execute(
                select(Membership).where(
                    Membership.project_id == project_id,
                    Membership.user_id == user_id,
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            return {"role": row.role, "joinedAt": row.joined_at}

    def set_role(self, project: dict, user: dict, role: str) -> None:
        with self._session() as session:
            row = session.execute(
                select(Membership).where(
                    Membership.project_id == project["id"],
                    Membership.user_id == user["id"],
                )
            ).scalar_one()
            row.role = role
            session.commit()

    def is_member(self, project: dict, user: dict) -> bool:
        return self.get_membership(project["id"], user["id"]) is not None

    def get_role(self, project: dict, user: dict) -> str | None:
        rec = self.get_membership(project["id"], user["id"])
        return rec["role"] if rec else None

    def list_members(self, project: dict) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(Membership, User)
                .join(User, User.id == Membership.user_id)
                .where(Membership.project_id == project["id"])
                .order_by(Membership.joined_at)
            ).all()
            return [self._member_dict(user_row, membership) for membership, user_row in rows]

    def list_other_members(self, project_id: str, exclude_user_id: str) -> list[str]:
        with self._session() as session:
            rows = session.execute(
                select(Membership.user_id).where(
                    Membership.project_id == project_id,
                    Membership.user_id != exclude_user_id,
                )
            ).scalars().all()
            return list(rows)

    def list_membership_admin_ids(self, project_id: str) -> list[str]:
        with self._session() as session:
            rows = session.execute(
                select(Membership.user_id).where(
                    Membership.project_id == project_id,
                    Membership.role == "admin",
                )
            ).scalars().all()
            return list(rows)

    def member_ids(self, project: dict) -> set[str]:
        with self._session() as session:
            rows = session.execute(
                select(Membership.user_id).where(Membership.project_id == project["id"])
            ).scalars().all()
            return set(rows)

    def member_dict(self, project: dict, user: dict) -> dict:
        with self._session() as session:
            membership = session.execute(
                select(Membership).where(
                    Membership.project_id == project["id"],
                    Membership.user_id == user["id"],
                )
            ).scalar_one()
            user_row = session.get(User, user["id"])
            return self._member_dict(user_row, membership)

    def user_project_ids(self, user_id: str) -> set[str]:
        with self._session() as session:
            rows = session.execute(
                select(Membership.project_id).where(Membership.user_id == user_id)
            ).scalars().all()
            return set(rows)

    def user_admins_any(self, user: dict) -> bool:
        with self._session() as session:
            row = session.execute(
                select(Membership.id).where(
                    Membership.user_id == user["id"],
                    Membership.role == "admin",
                )
            ).scalars().first()
            return row is not None

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def _insert_project(
        self,
        session: Session,
        pid: str,
        name: str,
        key: str,
        description: str,
        color: str,
        creator_id: str,
        *,
        icon: str | None = None,
        status: str = "active",
        archived_at: datetime.datetime | None = None,
        next_card_number: int = 1,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> dict:
        now = utcnow()
        project = Project(
            id=pid,
            name=name,
            key=key,
            description=description,
            color=color,
            icon=icon or key[0],
            status=status,
            archived=status == "archived",
            creator_id=creator_id,
            created_at=created_at or now,
            updated_at=updated_at or now,
            archived_at=archived_at,
            next_card_number=next_card_number,
        )
        session.add(project)
        return self._project_row(project)

    def create_project(
        self, creator: dict, name: str, description: str, color: str | None = None
    ) -> dict:
        key = derive_key(name)
        with self._session() as session:
            project = self._insert_project(
                session,
                self._next_id(session, "project"),
                name,
                key,
                description,
                color or PALETTE[hash(name) % len(PALETTE)],
                creator["id"],
            )
            session.add(
                Membership(
                    project_id=project["id"],
                    user_id=creator["id"],
                    role="admin",
                    joined_at=utcnow(),
                )
            )
            for col_name in ("To Do", "In Progress", "Done"):
                self._add_column(session, project, col_name)
            session.commit()
            return project

    def project_to_dict(self, project: dict) -> dict:
        return {**project, "members": self.list_members(project)}

    def list_projects_for_user(
        self, user_id: str, *, include_archived: bool = True
    ) -> list[dict]:
        with self._session() as session:
            project_ids = set(
                session.execute(
                    select(Membership.project_id).where(Membership.user_id == user_id)
                ).scalars()
            )
            if not project_ids:
                return []
            rows = session.execute(
                select(Project).where(Project.id.in_(project_ids))
            ).scalars().all()
            by_id = {row.id: self._project_row(row) for row in rows}
            out = [
                by_id[pid]
                for pid in sorted(project_ids)
                if pid in by_id
            ]
            if not include_archived:
                out = [p for p in out if not p["archived"]]
            return out

    def get_project(self, project_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(Project, project_id)
            return self._project_row(row) if row else None

    def update_project(self, project: dict, fields: dict[str, Any]) -> dict:
        with self._session() as session:
            row = session.get(Project, project["id"])
            for k in ("name", "description", "color"):
                if k in fields:
                    setattr(row, k, fields[k])
            if "name" in fields:
                row.icon = derive_key(fields["name"])[0]
            row.updated_at = utcnow()
            session.commit()
            return self._project_row(row)

    def archive_project(self, project: dict) -> dict:
        with self._session() as session:
            row = session.get(Project, project["id"])
            row.status = "archived"
            row.archived = True
            row.archived_at = utcnow()
            row.updated_at = utcnow()
            session.commit()
            return self._project_row(row)

    def restore_project(self, project: dict) -> dict:
        with self._session() as session:
            row = session.get(Project, project["id"])
            row.status = "active"
            row.archived = False
            row.archived_at = None
            row.updated_at = utcnow()
            session.commit()
            return self._project_row(row)

    def delete_project(self, project: dict) -> None:
        pid = project["id"]
        with self._session() as session:
            card_ids = set(
                session.execute(
                    select(Card.id).where(Card.project_id == pid)
                ).scalars()
            )
            session.execute(delete(BoardColumn).where(BoardColumn.project_id == pid))
            if card_ids:
                session.execute(delete(Comment).where(Comment.card_id.in_(card_ids)))
                session.execute(
                    delete(Relationship).where(
                        Relationship.source_card_id.in_(card_ids)
                        | Relationship.target_card_id.in_(card_ids)
                    )
                )
                session.execute(delete(Card).where(Card.id.in_(card_ids)))
            session.execute(delete(Membership).where(Membership.project_id == pid))
            session.execute(delete(Invite).where(Invite.project_id == pid))
            session.execute(delete(Project).where(Project.id == pid))
            session.commit()

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    def _add_column(
        self,
        session: Session,
        project: dict,
        name: str,
        *,
        color: str = DEFAULT_COLUMN_COLOR,
    ) -> dict:
        positions = list(
            session.execute(
                select(BoardColumn.position).where(BoardColumn.project_id == project["id"])
            ).scalars()
        )
        position = max(positions) + 1 if positions else 0
        now = utcnow()
        col = BoardColumn(
            id=self._next_id(session, "column"),
            project_id=project["id"],
            name=name,
            color=color,
            position=position,
            created_at=now,
            updated_at=now,
        )
        session.add(col)
        return self._column_row(col)

    def list_columns(self, project_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(BoardColumn)
                .where(BoardColumn.project_id == project_id)
                .order_by(BoardColumn.position)
            ).scalars().all()
            return [self._column_row(row) for row in rows]

    def get_column(self, column_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(BoardColumn, column_id)
            return self._column_row(row) if row else None

    def create_column(self, project: dict, name: str) -> dict:
        with self._session() as session:
            col = self._add_column(session, project, name)
            session.commit()
            return col

    def update_column(
        self, column: dict, *, name: str | None = None, position: int | None = None
    ) -> dict:
        with self._session() as session:
            row = session.get(BoardColumn, column["id"])
            if name is not None:
                row.name = name
            if position is not None:
                others = session.execute(
                    select(BoardColumn)
                    .where(BoardColumn.project_id == row.project_id)
                    .order_by(BoardColumn.position, BoardColumn.id)
                ).scalars().all()
                others = [c for c in others if c.id != row.id]
                position = min(max(position, 0), len(others))
                others.insert(position, row)
                for i, c in enumerate(others):
                    c.position = i
            row.updated_at = utcnow()
            session.commit()
            return self._column_row(row)

    def delete_column(self, column: dict, move_to: dict | None = None) -> None:
        with self._session() as session:
            if move_to is not None:
                cards = session.execute(
                    select(Card).where(Card.column_id == column["id"])
                ).scalars().all()
                now = utcnow()
                for card in cards:
                    card.column_id = move_to["id"]
                    card.updated_at = now
                self._renumber_cards(session, move_to["id"])
            self._renumber_cards(session, column["id"])
            session.execute(delete(BoardColumn).where(BoardColumn.id == column["id"]))
            session.commit()

    def _renumber_cards(self, session: Session, column_id: str) -> None:
        cards = session.execute(
            select(Card)
            .where(Card.column_id == column_id)
            .order_by(Card.position, Card.id)
        ).scalars().all()
        for i, c in enumerate(cards):
            c.position = i

    # ------------------------------------------------------------------
    # Cards
    # ------------------------------------------------------------------

    def list_cards(self, project_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(Card).where(Card.project_id == project_id)
            ).scalars().all()
            return [self._card_row(row) for row in rows]

    def list_cards_in_column(self, column_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(Card).where(Card.column_id == column_id)
            ).scalars().all()
            return [self._card_row(row) for row in rows]

    def get_card(self, card_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(Card, card_id)
            return self._card_row(row) if row else None

    def create_card(
        self,
        project: dict,
        column: dict,
        *,
        title: str,
        description: str,
        priority: str,
        assignee_id: str | None,
        due_date: datetime.date | None,
        labels: list[str],
        creator_id: str,
    ) -> dict:
        with self._session() as session:
            project_row = session.get(Project, project["id"])
            number = project_row.next_card_number
            project_row.next_card_number = number + 1
            card_id = f"{project_row.key}-{number}"
            now = utcnow()
            positions = set(
                session.execute(
                    select(Card.position).where(Card.column_id == column["id"])
                ).scalars()
            )
            card = Card(
                id=card_id,
                project_id=project["id"],
                column_id=column["id"],
                title=title,
                description=description,
                priority=priority,
                assignee_id=assignee_id,
                due_date=due_date,
                labels=list(labels),
                creator_id=creator_id,
                position=max(positions, default=0) + 1 if positions else 0,
                created_at=now,
                updated_at=now,
            )
            session.add(card)
            session.commit()
            return self._card_row(card)

    def update_card(self, card: dict, fields: dict[str, Any]) -> dict:
        with self._session() as session:
            row = session.get(Card, card["id"])
            for k in ("title", "description", "priority", "assigneeId", "dueDate", "labels"):
                if k in fields:
                    if k == "labels":
                        row.labels = list(fields[k] or [])
                    else:
                        setattr(row, {"assigneeId": "assignee_id", "dueDate": "due_date"}.get(k, k), fields[k])
            row.updated_at = utcnow()
            session.commit()
            return self._card_row(row)

    def move_card(
        self, card: dict, new_column: dict, position: int | None = None
    ) -> dict:
        with self._session() as session:
            row = session.get(Card, card["id"])
            old_column_id = row.column_id
            row.column_id = new_column["id"]
            same_column = old_column_id == new_column["id"]
            others = session.execute(
                select(Card)
                .where(Card.column_id == new_column["id"], Card.id != row.id)
                .order_by(Card.position, Card.id)
            ).scalars().all()
            if position is None:
                others.append(row)
            else:
                pos = min(max(position, 0), len(others))
                others.insert(pos, row)
            for i, c in enumerate(others):
                c.position = i
            if not same_column:
                self._renumber_cards(session, old_column_id)
            row.updated_at = utcnow()
            session.commit()
            return self._card_row(row)

    def card_to_dict(self, card: dict) -> dict:
        with self._session() as session:
            blocked_by = list(
                session.execute(
                    select(Relationship.source_card_id).where(
                        Relationship.target_card_id == card["id"]
                    )
                ).scalars()
            )
            blocking = list(
                session.execute(
                    select(Relationship.target_card_id).where(
                        Relationship.source_card_id == card["id"]
                    )
                ).scalars()
            )
            comment_count = session.execute(
                select(Comment.id).where(Comment.card_id == card["id"])
            ).scalars().all()
            return {
                **card,
                "blockedBy": blocked_by,
                "blocking": blocking,
                "commentCount": len(comment_count),
            }

    def card_relationships(self, card: dict) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(Relationship).where(
                    (Relationship.source_card_id == card["id"])
                    | (Relationship.target_card_id == card["id"])
                )
            ).scalars().all()
            return [self._rel_row(row) for row in rows]

    def delete_card(
        self,
        card: dict,
        *,
        resolution: str | None = None,
        reconnect_to: str | None = None,
    ) -> None:
        card_id = card["id"]
        with self._session() as session:
            if resolution == "delete":
                session.execute(
                    delete(Relationship).where(
                        (Relationship.source_card_id == card_id)
                        | (Relationship.target_card_id == card_id)
                    )
                )
            elif resolution == "reconnect" and reconnect_to:
                rels = session.execute(
                    select(Relationship).where(
                        (Relationship.source_card_id == card_id)
                        | (Relationship.target_card_id == card_id)
                    )
                ).scalars().all()
                seen: set[tuple[str, str]] = set()
                for rel in rels:
                    if rel.source_card_id == card_id:
                        rel.source_card_id = reconnect_to
                    elif rel.target_card_id == card_id:
                        rel.target_card_id = reconnect_to
                    if (rel.source_card_id, rel.target_card_id) in seen:
                        session.delete(rel)
                    else:
                        seen.add((rel.source_card_id, rel.target_card_id))
            card_row = session.get(Card, card_id)
            column_id = card_row.column_id
            session.execute(delete(Comment).where(Comment.card_id == card_id))
            session.execute(delete(Card).where(Card.id == card_id))
            self._renumber_cards(session, column_id)
            session.commit()

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def add_comment(self, card: dict, author_id: str, body: str) -> dict:
        now = utcnow()
        with self._session() as session:
            comment = Comment(
                id=self._next_id(session, "comment"),
                card_id=card["id"],
                author_id=author_id,
                body=body,
                created_at=now,
                updated_at=now,
                edited_at=None,
            )
            session.add(comment)
            session.commit()
            return self._comment_row(comment)

    def get_comment(self, comment_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(Comment, comment_id)
            return self._comment_row(row) if row else None

    def list_comments(self, card_id: str) -> list[dict]:
        with self._session() as session:
            rows = session.execute(
                select(Comment)
                .where(Comment.card_id == card_id)
                .order_by(Comment.created_at, Comment.id)
            ).scalars().all()
            return [self._comment_row(row) for row in rows]

    def list_comments_for_cards(self, card_ids: set[str]) -> list[dict]:
        if not card_ids:
            return []
        with self._session() as session:
            rows = session.execute(
                select(Comment).where(Comment.card_id.in_(card_ids))
            ).scalars().all()
            return [self._comment_row(row) for row in rows]

    def update_comment(self, comment: dict, body: str) -> dict:
        now = utcnow()
        with self._session() as session:
            row = session.get(Comment, comment["id"])
            row.body = body
            row.edited_at = now
            row.updated_at = now
            session.commit()
            return self._comment_row(row)

    def delete_comment(self, comment: dict) -> None:
        with self._session() as session:
            session.execute(delete(Comment).where(Comment.id == comment["id"]))
            session.commit()

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    def list_relationship_set(self, card: dict) -> dict:
        with self._session() as session:
            blocked_by_rows = session.execute(
                select(Relationship)
                .where(Relationship.target_card_id == card["id"])
                .order_by(Relationship.created_at, Relationship.id)
            ).scalars().all()
            blocking_rows = session.execute(
                select(Relationship)
                .where(Relationship.source_card_id == card["id"])
                .order_by(Relationship.created_at, Relationship.id)
            ).scalars().all()
            return {
                "blockedBy": [self._rel_row(r) for r in blocked_by_rows],
                "blocking": [self._rel_row(r) for r in blocking_rows],
            }

    def get_relationship(self, source_id: str, target_id: str) -> dict | None:
        with self._session() as session:
            row = session.execute(
                select(Relationship).where(
                    Relationship.source_card_id == source_id,
                    Relationship.target_card_id == target_id,
                )
            ).scalar_one_or_none()
            return self._rel_row(row) if row else None

    def create_relationship(self, source: dict, target: dict) -> dict:
        now = utcnow()
        with self._session() as session:
            rel = Relationship(
                id=self._next_id(session, "relationship"),
                source_card_id=source["id"],
                target_card_id=target["id"],
                type="blocks",
                created_at=now,
            )
            session.add(rel)
            session.commit()
            return self._rel_row(rel)

    def delete_relationship(self, source_id: str, target_id: str) -> bool:
        with self._session() as session:
            result = session.execute(
                delete(Relationship).where(
                    Relationship.source_card_id == source_id,
                    Relationship.target_card_id == target_id,
                )
            )
            session.commit()
            return result.rowcount > 0

    # ------------------------------------------------------------------
    # Invites
    # ------------------------------------------------------------------

    def create_invite(
        self, project: dict, created_by: dict, expires_in_days: int
    ) -> tuple[str, dict]:
        now = utcnow()
        expires_at = now + datetime.timedelta(days=expires_in_days)
        with self._session() as session:
            active = session.execute(
                select(Invite).where(
                    Invite.project_id == project["id"],
                    Invite.revoked.is_(False),
                    Invite.expires_at > now,
                )
            ).scalars().all()
            for invite in active:
                invite.revoked = True
            token = secrets.token_urlsafe(32)
            hashed = _sha256_hex(token)
            session.add(
                Invite(
                    token_hash=hashed,
                    project_id=project["id"],
                    created_by=created_by["id"],
                    expires_at=expires_at,
                    revoked=False,
                    created_at=now,
                )
            )
            session.commit()
            invite = {"expiresAt": expires_at}
            return token, invite

    def accept_invite(self, token: str) -> dict | None:
        with self._session() as session:
            rec = session.get(Invite, _sha256_hex(token))
            if rec is None:
                return None
            if rec.revoked or rec.expires_at <= utcnow():
                return None
            project = session.get(Project, rec.project_id)
            return self._project_row(project) if project else None

    def transfer_admin(self, project: dict, old_creator: dict, new_creator: dict) -> dict:
        with self._session() as session:
            project_row = session.get(Project, project["id"])
            project_row.creator_id = new_creator["id"]
            project_row.updated_at = utcnow()
            old_membership = session.execute(
                select(Membership).where(
                    Membership.project_id == project["id"],
                    Membership.user_id == old_creator["id"],
                )
            ).scalar_one()
            old_membership.role = "member"
            session.commit()
            return self._project_row(project_row)

    # ------------------------------------------------------------------
    # Account deletion
    # ------------------------------------------------------------------

    def delete_user(self, user: dict) -> None:
        uid = user["id"]
        with self._session() as session:
            session.execute(delete(Membership).where(Membership.user_id == uid))
            cards = session.execute(
                select(Card).where(Card.assignee_id == uid)
            ).scalars().all()
            now = utcnow()
            for card in cards:
                card.assignee_id = None
                card.updated_at = now
            session.execute(delete(User).where(User.id == uid))
            session.commit()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, user_id: str, q: str) -> list[dict]:
        term = q.strip().lower()
        if not term:
            return []
        with self._session() as session:
            project_ids = sorted(
                session.execute(
                    select(Membership.project_id).where(Membership.user_id == user_id)
                ).scalars()
            )
            results: list[dict] = []
            card_results: list[dict] = []
            if project_ids:
                projects = session.execute(
                    select(Project).where(Project.id.in_(project_ids))
                ).scalars().all()
                project_by_id = {p.id: p for p in projects}
                cards = session.execute(
                    select(Card).where(Card.project_id.in_(project_ids))
                ).scalars().all()
            else:
                project_by_id = {}
                cards = []

            for pid in project_ids:
                p = project_by_id.get(pid)
                if p is None:
                    continue
                blob = " ".join([p.name, p.key, p.description]).lower()
                if term in blob:
                    subtitle = "Archived project" if p.archived else f"{p.key} project"
                    results.append(
                        {
                            "type": "project",
                            "id": p.id,
                            "title": p.name,
                            "subtitle": subtitle,
                        }
                    )

            cards_by_project: dict[str, list[Card]] = {}
            for c in cards:
                cards_by_project.setdefault(c.project_id, []).append(c)
            for pid in project_ids:
                for c in cards_by_project.get(pid, []):
                    blob = " ".join([c.id, c.title, c.description]).lower()
                    if term in blob:
                        pname = project_by_id.get(c.project_id).name if c.project_id in project_by_id else ""
                        card_results.append(
                            {
                                "type": "card",
                                "id": c.id,
                                "title": c.title,
                                "subtitle": f"{c.id} · {pname}",
                            }
                        )

            results.extend(card_results)
            return results[:8]

    # ------------------------------------------------------------------
    # Seed
    # ------------------------------------------------------------------

    def seed(self) -> None:
        now = utcnow()
        with self._session() as session:
            if session.execute(select(User.id).limit(1)).first() is not None:
                session.close()
                return

            # --- Users ---
            self._insert_user(session, "u1", "Demo User", "demo@demo.dev", "password123", "#5f8f77")
            self._insert_user(session, "u2", "Mara Chen", "mara@demo.dev", "password123", "#db805e")
            self._insert_user(session, "u3", "Theo Alvarez", "theo@demo.dev", "password123", "#5f8f77")
            self._insert_user(session, "u4", "Inez Okafor", "inez@demo.dev", "password123", "#7a72ad")
            self._insert_user(session, "u5", "Rowan Bell", "rowan@demo.dev", "password123", "#c58b42")
            self._set_counter(session, "user", 5)

            # --- Projects ---
            p1 = self._insert_project(
                session,
                "p1", "Northstar", "NST",
                "A calmer way to see the work that moves the team forward.",
                "#5f8f77",
                "u1",
                next_card_number=148,
            )
            p2 = self._insert_project(
                session,
                "p2", "Field notes", "FLD",
                "Research threads and customer signals.",
                "#c58b42",
                "u1",
                next_card_number=25,
            )
            p3 = self._insert_project(
                session,
                "p3", "Orbit / archive", "ORB",
                "Previous experiments and decisions.",
                "#7a72ad",
                "u1",
                status="archived",
                archived_at=now - datetime.timedelta(days=18),
            )
            self._set_counter(session, "project", 3)

            # --- Memberships ---
            def _member(project_id: str, user_id: str, role: str, days: int) -> None:
                session.add(
                    Membership(
                        project_id=project_id,
                        user_id=user_id,
                        role=role,
                        joined_at=now - datetime.timedelta(days=days),
                    )
                )

            _member("p1", "u1", "admin", 30)
            _member("p1", "u2", "admin", 28)
            _member("p1", "u3", "member", 28)
            _member("p1", "u4", "member", 27)
            _member("p1", "u5", "member", 27)
            _member("p2", "u1", "admin", 20)
            _member("p2", "u2", "member", 19)
            _member("p2", "u3", "member", 19)
            _member("p3", "u1", "admin", 35)
            _member("p3", "u2", "member", 34)

            # --- Columns ---
            c1 = self._add_column(session, p1, "Backlog")
            c2 = self._add_column(session, p1, "In progress")
            c3 = self._add_column(session, p1, "Review")
            c4 = self._add_column(session, p1, "Shipped")
            c5 = self._add_column(session, p2, "Inbox")
            c6 = self._add_column(session, p2, "Exploring")
            c7 = self._add_column(session, p2, "Captured")
            c8 = self._add_column(session, p3, "Backlog")
            c9 = self._add_column(session, p3, "Done")
            self._set_counter(session, "column", 9)

            def _d(days: int) -> datetime.date:
                return (now + datetime.timedelta(days=days)).date()

            def _dt(days: int) -> datetime.datetime:
                return now + datetime.timedelta(days=days)

            def _card(
                card_id: str,
                project_id: str,
                column_id: str,
                title: str,
                description: str,
                priority: str,
                assignee_id: str | None,
                due_date: datetime.date | None,
                labels: list[str],
                creator_id: str,
                position: int,
            ) -> None:
                session.add(
                    Card(
                        id=card_id,
                        project_id=project_id,
                        column_id=column_id,
                        title=title,
                        description=description,
                        priority=priority,
                        assignee_id=assignee_id,
                        due_date=due_date,
                        labels=labels,
                        creator_id=creator_id,
                        position=position,
                        created_at=_dt(-9),
                        updated_at=_dt(-1),
                    )
                )

            # --- Cards (p1 / NST) ---
            _card("NST-142", "p1", c1["id"], 'Decide what "ready" means',
                  "A small checklist for work entering the flow, so context does not disappear at handoff.",
                  "high", "u2", _d(2), ["Process"], "u1", 0)
            _card("NST-138", "p1", c1["id"], "Audit the empty states",
                  "Make the first moment in a new project feel useful rather than blank.",
                  "medium", "u4", None, ["UX"], "u1", 1)
            _card("NST-145", "p1", c1["id"], "Name the release ritual",
                  "A lightweight weekly checkpoint for the team to look back before moving forward.",
                  "low", None, _d(6), ["Team"], "u1", 2)
            _card("NST-141", "p1", c2["id"], "Trim the board to the signal",
                  "Remove the fields that ask for busywork. Keep just enough shape to hold the story.",
                  "urgent", "u3", _d(-1), ["Product"], "u1", 0)
            _card("NST-147", "p1", c2["id"], "Map the first-run path",
                  "Walk a new teammate from open question to shipped work in under five minutes.",
                  "high", "u4", _d(3), ["UX"], "u1", 1)
            _card("NST-136", "p1", c3["id"], "Copy pass: project switcher",
                  "The switcher should make the active project and its state immediately clear.",
                  "medium", "u2", _d(4), ["Writing"], "u1", 0)
            _card("NST-129", "p1", c4["id"], "Define the team promise",
                  "A concise statement that keeps the workspace opinionated.",
                  "low", "u3", None, ["Strategy"], "u1", 0)
            # --- Cards (p2 / FLD) ---
            _card("FLD-24", "p2", c5["id"], "Ask three teams about handoffs",
                  "Listen for where context drops between conversation and action.",
                  "high", "u2", None, ["Research"], "u1", 0)
            _card("FLD-19", "p2", c6["id"], "Cluster the recurring friction",
                  "Turn the raw notes into a few patterns we can actually respond to.",
                  "medium", "u4", None, ["Research"], "u1", 0)
            _card("FLD-11", "p2", c7["id"], "Share the first readout",
                  "A short, honest note with what we know and what we still need to learn.",
                  "low", "u2", None, ["Writing"], "u1", 0)

            # --- Comments ---
            session.add(
                Comment(
                    id="cmt-1", card_id="NST-141", author_id="u2",
                    body="The cut feels right. Keep the rationale in the decision log.",
                    created_at=_dt(-2), updated_at=_dt(-2), edited_at=None,
                )
            )
            session.add(
                Comment(
                    id="cmt-2", card_id="NST-141", author_id="u3",
                    body="I can take the first pass after today's pairing session.",
                    created_at=_dt(-1), updated_at=_dt(-1), edited_at=None,
                )
            )
            self._set_counter(session, "comment", 2)

            # --- Relationships ---
            session.add(
                Relationship(
                    id="rel-1",
                    source_card_id="NST-141",
                    target_card_id="NST-147",
                    type="blocks",
                    created_at=_dt(-1),
                )
            )
            self._set_counter(session, "relationship", 1)

            session.commit()