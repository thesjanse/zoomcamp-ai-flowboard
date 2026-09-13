from fastapi import APIRouter, Depends, HTTPException, Response

from ..models import AddCommentInput, Comment, UpdateCommentInput
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_member

router = APIRouter(tags=["comments"])


def _get_comment_with_card(
    store: Store, comment_id: str, user: dict
) -> tuple[dict, dict, dict]:
    comment = store.get_comment(comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    card = store.get_card(comment["cardId"])
    if card is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    project = get_project_or_404(store, card["projectId"])
    require_member(store, project, user)
    return comment, card, project


@router.get("/cards/{card_id}/comments", response_model=list[Comment])
def list_comments(
    card_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[dict]:
    card = store.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found or no access")
    project = get_project_or_404(store, card["projectId"])
    require_member(store, project, user)
    return store.list_comments(card_id)


@router.post(
    "/cards/{card_id}/comments",
    response_model=Comment,
    status_code=201,
)
def add_comment(
    card_id: str,
    payload: AddCommentInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    card = store.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found or no access")
    project = get_project_or_404(store, card["projectId"])
    require_member(store, project, user)
    return store.add_comment(card, user["id"], payload.body)


@router.patch("/comments/{comment_id}", response_model=Comment)
def update_comment(
    comment_id: str,
    payload: UpdateCommentInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    comment, _card, _project = _get_comment_with_card(store, comment_id, user)
    if comment["authorId"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not the comment author")
    return store.update_comment(comment, payload.body)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    comment, card, project = _get_comment_with_card(store, comment_id, user)
    if comment["authorId"] != user["id"] and store.get_role(project, user) != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this comment")
    store.delete_comment(comment)
    return Response(status_code=204)