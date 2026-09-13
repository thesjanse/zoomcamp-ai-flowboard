from fastapi import APIRouter, Depends, HTTPException, Response

from ..models import (
    CreateRelationshipInput,
    Relationship,
    RelationshipSet,
)
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_member

router = APIRouter(tags=["relationships"])


def _get_card_and_project(
    store: Store, card_id: str, user: dict
) -> tuple[dict, dict]:
    card = store.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found or no access")
    project = get_project_or_404(store, card["projectId"])
    require_member(store, project, user)
    return card, project


@router.get(
    "/cards/{card_id}/relationships", response_model=RelationshipSet
)
def list_relationships(
    card_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    card, _project = _get_card_and_project(store, card_id, user)
    return store.list_relationship_set(card)


@router.post(
    "/cards/{card_id}/relationships",
    response_model=Relationship,
    status_code=201,
)
def create_relationship(
    card_id: str,
    payload: CreateRelationshipInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    source, project = _get_card_and_project(store, card_id, user)
    if payload.targetCardId == source["id"]:
        raise HTTPException(
            status_code=409, detail="A card cannot block itself"
        )
    target = store.get_card(payload.targetCardId)
    if target is None or target["projectId"] != project["id"]:
        raise HTTPException(
            status_code=409,
            detail="Only same-project relationships are allowed",
        )
    if store.get_relationship(source["id"], target["id"]) is not None:
        raise HTTPException(status_code=409, detail="Relationship already exists")
    return store.create_relationship(source, target)


@router.delete(
    "/cards/{card_id}/relationships/{target_card_id}",
    status_code=204,
)
def delete_relationship(
    card_id: str,
    target_card_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    card, _project = _get_card_and_project(store, card_id, user)
    store.delete_relationship(card["id"], target_card_id)
    return Response(status_code=204)