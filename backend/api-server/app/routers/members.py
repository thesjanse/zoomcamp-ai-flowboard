from fastapi import APIRouter, Depends, HTTPException, Response

from ..models import (
    Member,
    Project,
    TransferAdminInput,
    UpdateMemberRoleInput,
)
from ..store import Store
from ..auth import get_current_user
from ._helpers import (
    get_project_or_404,
    get_store,
    leave_project,
    require_admin,
    require_creator,
    require_member,
)

router = APIRouter(tags=["members"])


def _get_member_user(store: Store, project: dict, user_id: str) -> dict:
    target = store.get_user(user_id)
    if target is None or not store.is_member(project, target):
        raise HTTPException(status_code=404, detail="Member not found")
    return target


@router.get(
    "/projects/{project_id}/members", response_model=list[Member]
)
def list_members(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[dict]:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    return store.list_members(project)


@router.patch(
    "/projects/{project_id}/members/{user_id}",
    response_model=Member,
)
def update_member_role(
    project_id: str,
    user_id: str,
    payload: UpdateMemberRoleInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    target = _get_member_user(store, project, user_id)
    current_role = store.get_role(project, target)
    if payload.role == current_role:
        return store.member_dict(project, target)
    if payload.role == "member" and current_role == "admin":
        if target["id"] == project["creatorId"]:
            raise HTTPException(
                status_code=403, detail="Cannot change the creator's role"
            )
        if user["id"] != project["creatorId"]:
            raise HTTPException(
                status_code=403, detail="Only the creator can remove an admin"
            )
    store.set_role(project, target, payload.role)
    return store.member_dict(project, target)


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=204,
)
def remove_member(
    project_id: str,
    user_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    target = _get_member_user(store, project, user_id)
    if target["id"] == user["id"]:
        leave_project(store, project, user)
        return Response(status_code=204)
    if target["id"] == project["creatorId"]:
        raise HTTPException(
            status_code=403, detail="The creator cannot be removed"
        )
    if store.get_role(project, target) == "admin" and user["id"] != project["creatorId"]:
        raise HTTPException(
            status_code=403, detail="Only the creator can remove an admin"
        )
    store.remove_member(project, target)
    return Response(status_code=204)


@router.post(
    "/projects/{project_id}/transfer",
    response_model=Project,
)
def transfer_admin(
    project_id: str,
    payload: TransferAdminInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_creator(store, project, user)
    target = store.get_user(payload.adminId)
    if target is None or store.get_role(project, target) != "admin":
        raise HTTPException(
            status_code=404, detail="Admin not found in project"
        )
    project = store.transfer_admin(project, user, target)
    return store.project_to_dict(project)


@router.post(
    "/projects/{project_id}/leave",
    status_code=204,
)
def leave(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    leave_project(store, project, user)
    return Response(status_code=204)