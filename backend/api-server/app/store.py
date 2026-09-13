"""In-memory data store and seed data.

The store holds all application state in plain Python dicts/lists so the
backend can run without a database.  ``seed()`` populates the store with
demo users, projects, columns, cards, comments, and a relationship so the
frontend has something to show immediately.
"""

from __future__ import annotations

import datetime
import hashlib
import itertools
import re
import secrets
from typing import Any

from .auth import hash_password

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
    def __init__(self, *, seed: bool = True) -> None:
        self.users: dict[str, dict] = {}
        self.projects: dict[str, dict] = {}
        self.columns: dict[str, dict] = {}
        self.cards: dict[str, dict] = {}
        self.comments: dict[str, dict] = {}
        self.relationships: list[dict] = []
        self.invites: dict[str, dict] = {}
        self.memberships: dict[tuple[str, str], dict] = {}
        self._counters: dict[str, int] = {}
        if seed:
            self.seed()

    # ------------------------------------------------------------------
    # ID helpers
    # ------------------------------------------------------------------

    def _nid(self, kind: str) -> str:
        self._counters.setdefault(kind, 0)
        self._counters[kind] += 1
        return f"{kind}-{self._counters[kind]}"

    def _set_counter(self, kind: str, value: int) -> None:
        self._counters[kind] = value

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_user(self, user_id: str | None) -> dict | None:
        if user_id is None:
            return None
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> dict | None:
        email_lower = email.lower()
        for u in self.users.values():
            if u["email"] == email_lower:
                return u
        return None

    def _insert_user(
        self,
        uid: str,
        name: str,
        email: str,
        password: str,
        color: str,
    ) -> dict:
        now = utcnow()
        user = {
            "id": uid,
            "name": name,
            "email": email.lower(),
            "initials": compute_initials(name),
            "color": color,
            "passwordHash": hash_password(password),
            "createdAt": now,
            "updatedAt": now,
        }
        self.users[uid] = user
        return user

    def create_user(self, name: str, email: str, password_hash: str) -> dict:
        uid = self._nid("user")
        now = utcnow()
        user = {
            "id": uid,
            "name": name,
            "email": email.lower(),
            "initials": compute_initials(name),
            "color": PALETTE[hash(uid) % len(PALETTE)],
            "passwordHash": password_hash,
            "createdAt": now,
            "updatedAt": now,
        }
        self.users[uid] = user
        return user

    def user_to_dict(self, user: dict) -> dict:
        return {k: user[k] for k in ("id", "name", "email", "createdAt", "updatedAt")}

    def user_display_name(self, user_id: str | None) -> str:
        u = self.users.get(user_id) if user_id else None
        return u["name"] if u else "Deleted user"

    # ------------------------------------------------------------------
    # Memberships
    # ------------------------------------------------------------------

    def add_member(
        self, project: dict, user: dict, role: str = "member", *, joined_at: datetime.datetime | None = None
    ) -> None:
        self.memberships[(project["id"], user["id"])] = {
            "role": role,
            "joinedAt": joined_at or utcnow(),
        }

    def remove_member(self, project: dict, user: dict) -> None:
        self.memberships.pop((project["id"], user["id"]), None)

    def get_membership(self, project_id: str, user_id: str) -> dict | None:
        return self.memberships.get((project_id, user_id))

    def is_member(self, project: dict, user: dict) -> bool:
        return (project["id"], user["id"]) in self.memberships

    def get_role(self, project: dict, user: dict) -> str | None:
        rec = self.memberships.get((project["id"], user["id"]))
        return rec["role"] if rec else None

    def list_members(self, project: dict) -> list[dict]:
        out = []
        for (pid, uid), rec in self.memberships.items():
            if pid != project["id"]:
                continue
            u = self.users.get(uid)
            if u is None:
                continue
            out.append(
                {
                    "id": u["id"],
                    "name": u["name"],
                    "initials": u["initials"],
                    "color": u["color"],
                    "role": rec["role"],
                    "joinedAt": rec["joinedAt"],
                }
            )
        out.sort(key=lambda m: m["joinedAt"])
        return out

    def member_ids(self, project: dict) -> set[str]:
        return {uid for (pid, uid) in self.memberships if pid == project["id"]}

    def member_dict(self, project: dict, user: dict) -> dict:
        rec = self.memberships[(project["id"], user["id"])]
        return {
            "id": user["id"],
            "name": user["name"],
            "initials": user["initials"],
            "color": user["color"],
            "role": rec["role"],
            "joinedAt": rec["joinedAt"],
        }

    def user_project_ids(self, user_id: str) -> set[str]:
        return {pid for (pid, uid) in self.memberships if uid == user_id}

    def user_admins_any(self, user: dict) -> bool:
        for (pid, uid), rec in self.memberships.items():
            if uid == user["id"] and rec["role"] == "admin":
                return True
        return False

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def _insert_project(
        self,
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
        project = {
            "id": pid,
            "name": name,
            "key": key,
            "description": description,
            "color": color,
            "icon": icon or key[0],
            "status": status,
            "archived": status == "archived",
            "creatorId": creator_id,
            "createdAt": created_at or now,
            "updatedAt": updated_at or now,
            "archivedAt": archived_at,
            "nextCardNumber": next_card_number,
        }
        self.projects[pid] = project
        return project

    def create_project(
        self, creator: dict, name: str, description: str, color: str | None = None
    ) -> dict:
        key = derive_key(name)
        project = self._insert_project(
            self._nid("project"),
            name,
            key,
            description,
            color or PALETTE[hash(name) % len(PALETTE)],
            creator["id"],
        )
        self.add_member(project, creator, role="admin")
        for col_name in ("To Do", "In Progress", "Done"):
            self._add_column(project, col_name)
        return project

    def project_to_dict(self, project: dict) -> dict:
        return {**project, "members": self.list_members(project)}

    def list_projects_for_user(
        self, user_id: str, *, include_archived: bool = True
    ) -> list[dict]:
        project_ids = {pid for (pid, uid) in self.memberships if uid == user_id}
        out = [
            self.projects[pid]
            for pid in sorted(project_ids)
            if pid in self.projects
        ]
        if not include_archived:
            out = [p for p in out if not p["archived"]]
        return out

    def get_project(self, project_id: str) -> dict | None:
        return self.projects.get(project_id)

    def update_project(self, project: dict, fields: dict[str, Any]) -> dict:
        for k in ("name", "description", "color"):
            if k in fields:
                project[k] = fields[k]
        if "name" in fields:
            project["icon"] = derive_key(fields["name"])[0]
        project["updatedAt"] = utcnow()
        return project

    def archive_project(self, project: dict) -> dict:
        project["status"] = "archived"
        project["archived"] = True
        project["archivedAt"] = utcnow()
        project["updatedAt"] = utcnow()
        return project

    def restore_project(self, project: dict) -> dict:
        project["status"] = "active"
        project["archived"] = False
        project["archivedAt"] = None
        project["updatedAt"] = utcnow()
        return project

    def delete_project(self, project: dict) -> None:
        pid = project["id"]
        col_ids = [cid for cid, c in self.columns.items() if c["projectId"] == pid]
        for cid in col_ids:
            del self.columns[cid]
        card_ids = [cid for cid, c in self.cards.items() if c["projectId"] == pid]
        for cid in card_ids:
            del self.cards[cid]
        self.comments = {k: v for k, v in self.comments.items() if v["cardId"] not in card_ids}
        self.relationships = [
            r
            for r in self.relationships
            if r["sourceCardId"] not in card_ids and r["targetCardId"] not in card_ids
        ]
        self.memberships = {
            k: v for k, v in self.memberships.items() if k[0] != pid
        }
        self.invites = {k: v for k, v in self.invites.items() if v["projectId"] != pid}
        del self.projects[pid]

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    def _add_column(
        self, project: dict, name: str, *, color: str = DEFAULT_COLUMN_COLOR
    ) -> dict:
        cid = self._nid("column")
        positions = [c["position"] for c in self.columns.values() if c["projectId"] == project["id"]]
        position = max(positions) + 1 if positions else 0
        now = utcnow()
        col = {
            "id": cid,
            "projectId": project["id"],
            "name": name,
            "color": color,
            "position": position,
            "createdAt": now,
            "updatedAt": now,
        }
        self.columns[cid] = col
        return col

    def list_columns(self, project_id: str) -> list[dict]:
        cols = [c for c in self.columns.values() if c["projectId"] == project_id]
        cols.sort(key=lambda c: c["position"])
        return cols

    def get_column(self, column_id: str) -> dict | None:
        return self.columns.get(column_id)

    def create_column(self, project: dict, name: str) -> dict:
        return self._add_column(project, name)

    def update_column(
        self, column: dict, *, name: str | None = None, position: int | None = None
    ) -> dict:
        if name is not None:
            column["name"] = name
        if position is not None:
            cols = [c for c in self.columns.values() if c["projectId"] == column["projectId"]]
            cols = [c for c in cols if c["id"] != column["id"]]
            position = min(max(position, 0), len(cols))
            cols.insert(position, column)
            for i, c in enumerate(cols):
                c["position"] = i
        column["updatedAt"] = utcnow()
        return column

    def delete_column(self, column: dict, move_to: dict | None = None) -> None:
        if move_to is not None:
            for card in [c for c in self.cards.values() if c["columnId"] == column["id"]]:
                card["columnId"] = move_to["id"]
                card["updatedAt"] = utcnow()
            self._renumber_cards(move_to["id"])
        self._renumber_cards(column["id"])
        del self.columns[column["id"]]

    def _renumber_cards(self, column_id: str) -> None:
        cards_in_col = [c for c in self.cards.values() if c["columnId"] == column_id]
        cards_in_col.sort(key=lambda c: (c["position"], c["id"]))
        for i, c in enumerate(cards_in_col):
            c["position"] = i

    # ------------------------------------------------------------------
    # Cards
    # ------------------------------------------------------------------

    def list_cards(self, project_id: str) -> list[dict]:
        return [c for c in self.cards.values() if c["projectId"] == project_id]

    def get_card(self, card_id: str) -> dict | None:
        return self.cards.get(card_id)

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
        number = project["nextCardNumber"]
        project["nextCardNumber"] += 1
        card_id = f"{project['key']}-{number}"
        now = utcnow()
        positions = [c["position"] for c in self.cards.values() if c["columnId"] == column["id"]]
        position = max(positions) + 1 if positions else 0
        card = {
            "id": card_id,
            "projectId": project["id"],
            "columnId": column["id"],
            "title": title,
            "description": description,
            "priority": priority,
            "assigneeId": assignee_id,
            "dueDate": due_date,
            "labels": list(labels),
            "creatorId": creator_id,
            "position": position,
            "createdAt": now,
            "updatedAt": now,
        }
        self.cards[card_id] = card
        return card

    def update_card(self, card: dict, fields: dict[str, Any]) -> dict:
        for k in ("title", "description", "priority", "assigneeId", "dueDate", "labels"):
            if k in fields:
                card[k] = fields[k]
        card["updatedAt"] = utcnow()
        return card

    def move_card(
        self, card: dict, new_column: dict, position: int | None = None
    ) -> dict:
        old_column_id = card["columnId"]
        card["columnId"] = new_column["id"]
        same_column = old_column_id == new_column["id"]
        others = [
            c
            for c in self.cards.values()
            if c["columnId"] == new_column["id"] and c["id"] != card["id"]
        ]
        others.sort(key=lambda c: (c["position"], c["id"]))
        if position is None:
            others.append(card)
        else:
            pos = min(max(position, 0), len(others))
            others.insert(pos, card)
        for i, c in enumerate(others):
            c["position"] = i
        if not same_column:
            self._renumber_cards(old_column_id)
        card["updatedAt"] = utcnow()
        return card

    def card_to_dict(self, card: dict) -> dict:
        blocked_by = [
            r["sourceCardId"]
            for r in self.relationships
            if r["targetCardId"] == card["id"]
        ]
        blocking = [
            r["targetCardId"]
            for r in self.relationships
            if r["sourceCardId"] == card["id"]
        ]
        comment_count = sum(
            1 for c in self.comments.values() if c["cardId"] == card["id"]
        )
        return {
            **card,
            "blockedBy": blocked_by,
            "blocking": blocking,
            "commentCount": comment_count,
        }

    def card_relationships(self, card: dict) -> list[dict]:
        return [
            r
            for r in self.relationships
            if r["sourceCardId"] == card["id"] or r["targetCardId"] == card["id"]
        ]

    def delete_card(
        self,
        card: dict,
        *,
        resolution: str | None = None,
        reconnect_to: str | None = None,
    ) -> None:
        card_id = card["id"]
        if resolution == "delete":
            self.relationships = [
                r
                for r in self.relationships
                if r["sourceCardId"] != card_id and r["targetCardId"] != card_id
            ]
        elif resolution == "reconnect" and reconnect_to:
            for r in self.relationships:
                if r["sourceCardId"] == card_id:
                    r["sourceCardId"] = reconnect_to
                elif r["targetCardId"] == card_id:
                    r["targetCardId"] = reconnect_to
            seen: set[tuple[str, str]] = set()
            keep: list[dict] = []
            for r in self.relationships:
                if (r["sourceCardId"], r["targetCardId"]) not in seen:
                    seen.add((r["sourceCardId"], r["targetCardId"]))
                    keep.append(r)
            self.relationships = keep
        card_column_id = card["columnId"]
        del self.cards[card_id]
        self.comments = {
            k: v for k, v in self.comments.items() if v["cardId"] != card_id
        }
        self._renumber_cards(card_column_id)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def add_comment(self, card: dict, author_id: str, body: str) -> dict:
        now = utcnow()
        comment = {
            "id": self._nid("comment"),
            "cardId": card["id"],
            "authorId": author_id,
            "body": body,
            "createdAt": now,
            "updatedAt": now,
            "editedAt": None,
        }
        self.comments[comment["id"]] = comment
        return comment

    def get_comment(self, comment_id: str) -> dict | None:
        return self.comments.get(comment_id)

    def list_comments(self, card_id: str) -> list[dict]:
        return [c for c in self.comments.values() if c["cardId"] == card_id]

    def update_comment(self, comment: dict, body: str) -> dict:
        comment["body"] = body
        comment["editedAt"] = utcnow()
        comment["updatedAt"] = utcnow()
        return comment

    def delete_comment(self, comment: dict) -> None:
        self.comments.pop(comment["id"], None)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    def list_relationship_set(self, card: dict) -> dict:
        blocked_by = [
            r for r in self.relationships if r["targetCardId"] == card["id"]
        ]
        blocking = [
            r for r in self.relationships if r["sourceCardId"] == card["id"]
        ]
        return {"blockedBy": blocked_by, "blocking": blocking}

    def get_relationship(self, source_id: str, target_id: str) -> dict | None:
        for r in self.relationships:
            if r["sourceCardId"] == source_id and r["targetCardId"] == target_id:
                return r
        return None

    def create_relationship(self, source: dict, target: dict) -> dict:
        now = utcnow()
        rel = {
            "id": self._nid("relationship"),
            "sourceCardId": source["id"],
            "targetCardId": target["id"],
            "type": "blocks",
            "createdAt": now,
        }
        self.relationships.append(rel)
        return rel

    def delete_relationship(self, source_id: str, target_id: str) -> bool:
        before = len(self.relationships)
        self.relationships = [
            r
            for r in self.relationships
            if not (r["sourceCardId"] == source_id and r["targetCardId"] == target_id)
        ]
        return len(self.relationships) < before

    # ------------------------------------------------------------------
    # Invites
    # ------------------------------------------------------------------

    def create_invite(
        self, project: dict, created_by: dict, expires_in_days: int
    ) -> tuple[str, dict]:
        now = utcnow()
        expires_at = now + datetime.timedelta(days=expires_in_days)
        for rec in self.invites.values():
            if (
                rec["projectId"] == project["id"]
                and not rec["revoked"]
                and rec["expiresAt"] > now
            ):
                rec["revoked"] = True
        token = secrets.token_urlsafe(32)
        hashed = _sha256_hex(token)
        invite = {
            "projectId": project["id"],
            "createdBy": created_by["id"],
            "expiresAt": expires_at,
            "revoked": False,
            "createdAt": now,
        }
        self.invites[hashed] = invite
        return token, invite

    def accept_invite(self, token: str) -> dict | None:
        rec = self.invites.get(_sha256_hex(token))
        if rec is None:
            return None
        if rec["revoked"] or rec["expiresAt"] <= utcnow():
            return None
        return self.projects.get(rec["projectId"])

    # ------------------------------------------------------------------
    # Account deletion
    # ------------------------------------------------------------------

    def delete_user(self, user: dict) -> None:
        uid = user["id"]
        self.memberships = {
            k: v for k, v in self.memberships.items() if k[1] != uid
        }
        for card in self.cards.values():
            if card.get("assigneeId") == uid:
                card["assigneeId"] = None
                card["updatedAt"] = utcnow()
        del self.users[uid]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, user_id: str, q: str) -> list[dict]:
        term = q.strip().lower()
        if not term:
            return []
        project_ids = self.user_project_ids(user_id)
        results: list[dict] = []
        for pid in sorted(project_ids):
            p = self.projects.get(pid)
            if p is None:
                continue
            blob = " ".join([p["name"], p["key"], p["description"]]).lower()
            if term in blob:
                subtitle = "Archived project" if p["archived"] else f"{p['key']} project"
                results.append(
                    {
                        "type": "project",
                        "id": p["id"],
                        "title": p["name"],
                        "subtitle": subtitle,
                    }
                )
        card_results: list[dict] = []
        for c in self.cards.values():
            if c["projectId"] not in project_ids:
                continue
            blob = " ".join([c["id"], c["title"], c["description"]]).lower()
            if term in blob:
                pname = self.projects.get(c["projectId"], {}).get("name", "")
                card_results.append(
                    {
                        "type": "card",
                        "id": c["id"],
                        "title": c["title"],
                        "subtitle": f"{c['id']} · {pname}",
                    }
                )
        results.extend(card_results)
        return results[:8]

    # ------------------------------------------------------------------
    # Seed
    # ------------------------------------------------------------------

    def seed(self) -> None:
        now = utcnow()

        # --- Users ---
        self._insert_user("u1", "Demo User", "demo@demo.dev", "password123", "#5f8f77")
        self._insert_user("u2", "Mara Chen", "mara@demo.dev", "password123", "#db805e")
        self._insert_user("u3", "Theo Alvarez", "theo@demo.dev", "password123", "#5f8f77")
        self._insert_user("u4", "Inez Okafor", "inez@demo.dev", "password123", "#7a72ad")
        self._insert_user("u5", "Rowan Bell", "rowan@demo.dev", "password123", "#c58b42")
        self._set_counter("user", 5)

        # --- Projects ---
        p1 = self._insert_project(
            "p1", "Northstar", "NST",
            "A calmer way to see the work that moves the team forward.",
            "#5f8f77",
            "u1",
            next_card_number=148,
        )
        p2 = self._insert_project(
            "p2", "Field notes", "FLD",
            "Research threads and customer signals.",
            "#c58b42",
            "u1",
            next_card_number=25,
        )
        p3 = self._insert_project(
            "p3", "Orbit / archive", "ORB",
            "Previous experiments and decisions.",
            "#7a72ad",
            "u1",
            status="archived",
            archived_at=now - datetime.timedelta(days=18),
        )
        self._set_counter("project", 3)

        # --- Memberships ---
        # p1: u1 admin (creator), u2 admin, u3-u5 member
        self.add_member(p1, self.users["u1"], role="admin", joined_at=now - datetime.timedelta(days=30))
        self.add_member(p1, self.users["u2"], role="admin", joined_at=now - datetime.timedelta(days=28))
        self.add_member(p1, self.users["u3"], role="member", joined_at=now - datetime.timedelta(days=28))
        self.add_member(p1, self.users["u4"], role="member", joined_at=now - datetime.timedelta(days=27))
        self.add_member(p1, self.users["u5"], role="member", joined_at=now - datetime.timedelta(days=27))
        # p2: u1 admin, u2 u3 members
        self.add_member(p2, self.users["u1"], role="admin", joined_at=now - datetime.timedelta(days=20))
        self.add_member(p2, self.users["u2"], role="member", joined_at=now - datetime.timedelta(days=19))
        self.add_member(p2, self.users["u3"], role="member", joined_at=now - datetime.timedelta(days=19))
        # p3: u1 admin, u2 member
        self.add_member(p3, self.users["u1"], role="admin", joined_at=now - datetime.timedelta(days=35))
        self.add_member(p3, self.users["u2"], role="member", joined_at=now - datetime.timedelta(days=34))

        # --- Columns ---
        c1 = self._add_column(p1, "Backlog")
        c2 = self._add_column(p1, "In progress")
        c3 = self._add_column(p1, "Review")
        c4 = self._add_column(p1, "Shipped")
        c5 = self._add_column(p2, "Inbox")
        c6 = self._add_column(p2, "Exploring")
        c7 = self._add_column(p2, "Captured")
        c8 = self._add_column(p3, "Backlog")
        c9 = self._add_column(p3, "Done")
        self._set_counter("column", 9)

        def _d(days: int) -> datetime.date:
            return (now + datetime.timedelta(days=days)).date()

        def _dt(days: int) -> datetime.datetime:
            return now + datetime.timedelta(days=days)

        # --- Cards (p1 / NST) ---
        self.cards["NST-142"] = {
            "id": "NST-142", "projectId": "p1", "columnId": c1["id"],
            "title": 'Decide what "ready" means',
            "description": "A small checklist for work entering the flow, so context does not disappear at handoff.",
            "priority": "high", "assigneeId": "u2", "dueDate": _d(2),
            "labels": ["Process"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-138"] = {
            "id": "NST-138", "projectId": "p1", "columnId": c1["id"],
            "title": "Audit the empty states",
            "description": "Make the first moment in a new project feel useful rather than blank.",
            "priority": "medium", "assigneeId": "u4", "dueDate": None,
            "labels": ["UX"], "creatorId": "u1", "position": 1,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-145"] = {
            "id": "NST-145", "projectId": "p1", "columnId": c1["id"],
            "title": "Name the release ritual",
            "description": "A lightweight weekly checkpoint for the team to look back before moving forward.",
            "priority": "low", "assigneeId": None, "dueDate": _d(6),
            "labels": ["Team"], "creatorId": "u1", "position": 2,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-141"] = {
            "id": "NST-141", "projectId": "p1", "columnId": c2["id"],
            "title": "Trim the board to the signal",
            "description": "Remove the fields that ask for busywork. Keep just enough shape to hold the story.",
            "priority": "urgent", "assigneeId": "u3", "dueDate": _d(-1),
            "labels": ["Product"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-147"] = {
            "id": "NST-147", "projectId": "p1", "columnId": c2["id"],
            "title": "Map the first-run path",
            "description": "Walk a new teammate from open question to shipped work in under five minutes.",
            "priority": "high", "assigneeId": "u4", "dueDate": _d(3),
            "labels": ["UX"], "creatorId": "u1", "position": 1,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-136"] = {
            "id": "NST-136", "projectId": "p1", "columnId": c3["id"],
            "title": "Copy pass: project switcher",
            "description": "The switcher should make the active project and its state immediately clear.",
            "priority": "medium", "assigneeId": "u2", "dueDate": _d(4),
            "labels": ["Writing"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["NST-129"] = {
            "id": "NST-129", "projectId": "p1", "columnId": c4["id"],
            "title": "Define the team promise",
            "description": "A concise statement that keeps the workspace opinionated.",
            "priority": "low", "assigneeId": "u3", "dueDate": None,
            "labels": ["Strategy"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        # --- Cards (p2 / FLD) ---
        self.cards["FLD-24"] = {
            "id": "FLD-24", "projectId": "p2", "columnId": c5["id"],
            "title": "Ask three teams about handoffs",
            "description": "Listen for where context drops between conversation and action.",
            "priority": "high", "assigneeId": "u2", "dueDate": None,
            "labels": ["Research"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["FLD-19"] = {
            "id": "FLD-19", "projectId": "p2", "columnId": c6["id"],
            "title": "Cluster the recurring friction",
            "description": "Turn the raw notes into a few patterns we can actually respond to.",
            "priority": "medium", "assigneeId": "u4", "dueDate": None,
            "labels": ["Research"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }
        self.cards["FLD-11"] = {
            "id": "FLD-11", "projectId": "p2", "columnId": c7["id"],
            "title": "Share the first readout",
            "description": "A short, honest note with what we know and what we still need to learn.",
            "priority": "low", "assigneeId": "u2", "dueDate": None,
            "labels": ["Writing"], "creatorId": "u1", "position": 0,
            "createdAt": _dt(-9), "updatedAt": _dt(-1),
        }

        # --- Comments ---
        self.comments["cmt-1"] = {
            "id": "cmt-1", "cardId": "NST-141", "authorId": "u2",
            "body": "The cut feels right. Keep the rationale in the decision log.",
            "createdAt": _dt(-2), "updatedAt": _dt(-2), "editedAt": None,
        }
        self.comments["cmt-2"] = {
            "id": "cmt-2", "cardId": "NST-141", "authorId": "u3",
            "body": "I can take the first pass after today's pairing session.",
            "createdAt": _dt(-1), "updatedAt": _dt(-1), "editedAt": None,
        }
        self._set_counter("comment", 2)

        # --- Relationships ---
        self.relationships.append({
            "id": "rel-1",
            "sourceCardId": "NST-141",
            "targetCardId": "NST-147",
            "type": "blocks",
            "createdAt": _dt(-1),
        })
        self._set_counter("relationship", 1)