from fastapi import APIRouter, Depends, HTTPException, Response

from ..models import (
    Card,
    CardInput,
    DeleteCardInput,
    MoveCardInput,
    UpdateCardInput,
)
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_member

router = APIRouter(tags=["cards"])


def _get_card_and_project(
    store: Store, card_id: str, user: dict
) -> tuple[dict, dict]:
    card = store.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found or no access")
    project = get_project_or_404(store, card["projectId"])
    require_member(store, project, user)
    return card, project


@router.post(
    "/projects/{project_id}/cards", response_model=Card, status_code=201
)
def create_card(
    project_id: str,
    payload: CardInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)
    column = store.get_column(payload.columnId)
    if column is None or column["projectId"] != project["id"]:
        raise HTTPException(
            status_code=422, detail="Column not found in project"
        )
    if payload.assigneeId is not None:
        assignee = store.get_user(payload.assigneeId)
        if assignee is None or not store.is_member(project, assignee):
            raise HTTPException(
                status_code=422, detail="Assignee must be a project member"
            )
    card = store.create_card(
        project,
        column,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assigneeId,
        due_date=payload.dueDate,
        labels=payload.labels,
        creator_id=user["id"],
    )
    return store.card_to_dict(card)


@router.get("/cards/{card_id}", response_model=Card)
def get_card(
    card_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    card, _project = _get_card_and_project(store, card_id, user)
    return store.card_to_dict(card)


@router.patch("/cards/{card_id}", response_model=Card)
def update_card(
    card_id: str,
    payload: UpdateCardInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    card, project = _get_card_and_project(store, card_id, user)
    fields = {k: getattr(payload, k) for k in payload.model_fields_set}
    if "assigneeId" in fields and fields["assigneeId"] is not None:
        assignee = store.get_user(fields["assigneeId"])
        if assignee is None or not store.is_member(project, assignee):
            raise HTTPException(
                status_code=422, detail="Assignee must be a project member"
            )
    card = store.update_card(card, fields)
    return store.card_to_dict(card)


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(
    card_id: str,
    payload: DeleteCardInput | None = None,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    card, _project = _get_card_and_project(store, card_id, user)
    resolution = payload.resolveRelationships if payload else None
    reconnect_to = payload.reconnectToCardId if payload else None
    if store.card_relationships(card):
        if resolution is None:
            raise HTTPException(
                status_code=409,
                detail="Card has relationships; resolve them before deleting",
            )
        if resolution == "reconnect":
            if reconnect_to is None:
                raise HTTPException(
                    status_code=409, detail="reconnectToCardId is required"
                )
            target = store.get_card(reconnect_to)
            if (
                target is None
                or target["projectId"] != card["projectId"]
                or target["id"] == card["id"]
            ):
                raise HTTPException(
                    status_code=409,
                    detail="reconnectToCardId must be a card in the same project",
                )
        store.delete_card(card, resolution=resolution, reconnect_to=reconnect_to)
    else:
        store.delete_card(card)
    return Response(status_code=204)


@router.post("/cards/{card_id}/move", response_model=Card)
def move_card(
    card_id: str,
    payload: MoveCardInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    card, project = _get_card_and_project(store, card_id, user)
    column = store.get_column(payload.columnId)
    if column is None or column["projectId"] != project["id"]:
        raise HTTPException(
            status_code=404, detail="Card or column not found or no access"
        )
    card = store.move_card(card, column, payload.position)
    return store.card_to_dict(card)