from fastapi import APIRouter, Depends, HTTPException, Response

from ..models import CreateInviteInput, Invite, Project
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_admin, require_member
from .. import config

router = APIRouter(tags=["invites"])


@router.post(
    "/projects/{project_id}/invites",
    response_model=Invite,
    status_code=201,
)
def create_invite(
    project_id: str,
    payload: CreateInviteInput | None = None,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    days = config.INVITE_DEFAULT_DAYS
    if payload and payload.expiresInDays is not None:
        days = payload.expiresInDays
    token, invite = store.create_invite(project, user, days)
    return {"token": token, "expiresAt": invite["expiresAt"]}


@router.post(
    "/invites/{token}/accept",
    response_model=Project,
)
def accept_invite(
    token: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = store.accept_invite(token)
    if project is None:
        raise HTTPException(status_code=410, detail="Invite expired or revoked")
    if not store.is_member(project, user):
        store.add_member(project, user, role="member")
    return store.project_to_dict(project)