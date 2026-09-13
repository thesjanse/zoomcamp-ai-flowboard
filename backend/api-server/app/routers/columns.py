from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ..models import BoardColumn, CreateColumnInput, UpdateColumnInput
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_admin, require_member

router = APIRouter(tags=["columns"])


def _get_column_and_project(
    store: Store,
    column_id: str,
    user: dict,
) -> tuple[dict, dict]:
    column = store.get_column(column_id)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    project = get_project_or_404(store, column["projectId"])
    require_member(store, project, user)
    return column, project


@router.get(
    "/projects/{project_id}/columns", response_model=list[BoardColumn]
)
def list_columns(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[dict]:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    return store.list_columns(project["id"])


@router.post(
    "/projects/{project_id}/columns",
    response_model=BoardColumn,
    status_code=201,
)
def create_column(
    project_id: str,
    payload: CreateColumnInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    require_admin(store, project, user)
    existing = store.list_columns(project["id"])
    if len(existing) >= 7:
        raise HTTPException(
            status_code=409, detail="Maximum of 7 columns reached"
        )
    return store.create_column(project, payload.name)


@router.patch("/columns/{column_id}", response_model=BoardColumn)
def update_column(
    column_id: str,
    payload: UpdateColumnInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    column, project = _get_column_and_project(store, column_id, user)
    require_admin(store, project, user)
    return store.update_column(
        column,
        name=payload.name,
        position=payload.position,
    )


@router.delete("/columns/{column_id}", status_code=204)
def delete_column(
    column_id: str,
    move_cards_to: str | None = Query(default=None, alias="moveCardsTo"),
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    column, project = _get_column_and_project(store, column_id, user)
    require_admin(store, project, user)
    existing = store.list_columns(project["id"])
    if len(existing) <= 1:
        raise HTTPException(
            status_code=409, detail="A project must keep at least one column"
        )
    cards_in_col = [c for c in store.cards.values() if c["columnId"] == column_id]
    if cards_in_col and move_cards_to is None:
        raise HTTPException(
            status_code=409,
            detail="Column contains cards; provide a moveCardsTo destination",
        )
    dest = None
    if move_cards_to is not None:
        dest = store.get_column(move_cards_to)
        if dest is None or dest["projectId"] != project["id"] or dest["id"] == column_id:
            raise HTTPException(
                status_code=409, detail="Invalid destination column"
            )
    store.delete_column(column, move_to=dest)
    return Response(status_code=204)