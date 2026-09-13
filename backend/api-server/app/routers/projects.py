from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ..models import CreateProjectInput, Project, UpdateProjectInput
from ..store import Store
from ..auth import get_current_user
from ._helpers import (
    get_project_or_404,
    get_store,
    require_admin,
    require_member,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects(
    include_archived: bool = Query(default=True, alias="includeArchived"),
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[dict]:
    projects = store.list_projects_for_user(
        user["id"], include_archived=include_archived
    )
    return [store.project_to_dict(p) for p in projects]


@router.post("", response_model=Project, status_code=201)
def create_project(
    payload: CreateProjectInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = store.create_project(
        user, payload.name, payload.description, payload.color
    )
    return store.project_to_dict(project)


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    return store.project_to_dict(project)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    payload: UpdateProjectInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    fields = {k: getattr(payload, k) for k in payload.model_fields_set}
    store.update_project(project, fields)
    return store.project_to_dict(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    if not project["archived"]:
        raise HTTPException(status_code=409, detail="Project is not archived")
    store.delete_project(project)
    return Response(status_code=204)


@router.post("/{project_id}/archive", response_model=Project)
def archive_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    store.archive_project(project)
    return store.project_to_dict(project)


@router.post("/{project_id}/restore", response_model=Project)
def restore_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    store.restore_project(project)
    return store.project_to_dict(project)