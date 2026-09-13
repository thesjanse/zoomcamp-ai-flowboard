"""Shared FastAPI dependencies and permission helpers for routers."""

from __future__ import annotations

from fastapi import HTTPException, Request

from ..store import Store


def get_store(request: Request) -> Store:
    return request.app.state.store


def get_project_or_404(store: Store, project_id: str) -> dict:
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_member(store: Store, project: dict, user: dict) -> None:
    if not store.is_member(project, user):
        raise HTTPException(status_code=404, detail="Project not found or no access")


def require_admin(store: Store, project: dict, user: dict) -> None:
    if store.get_role(project, user) != "admin":
        raise HTTPException(status_code=403, detail="Not a project admin")


def require_creator(store: Store, project: dict, user: dict) -> None:
    if project["creatorId"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the creator can perform this action")


def leave_project(store: Store, project: dict, user: dict) -> None:
    """Apply the leave rules from _docs/specs.md section 4.17."""
    if project["creatorId"] == user["id"]:
        others = [
            uid
            for (pid, uid) in store.memberships
            if pid == project["id"] and uid != user["id"]
        ]
        if others:
            raise HTTPException(
                status_code=409,
                detail="Creator must designate another admin before leaving",
            )
        store.remove_member(project, user)
        store.archive_project(project)
        return

    if store.get_role(project, user) == "admin":
        admins = [
            uid
            for (pid, uid), rec in store.memberships.items()
            if pid == project["id"] and rec["role"] == "admin" and uid != user["id"]
        ]
        if not admins:
            raise HTTPException(
                status_code=409, detail="Another admin must remain before leaving"
            )
    store.remove_member(project, user)