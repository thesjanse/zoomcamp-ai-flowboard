import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..models import BoardSnapshot, DUE_FILTER
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_project_or_404, get_store, require_member

router = APIRouter(tags=["board"])

_VALID_PRIORITIES = {"urgent", "high", "medium", "low"}


@router.get("/projects/{project_id}/board", response_model=BoardSnapshot)
def get_board(
    project_id: str,
    search: str | None = Query(default=None),
    priorities: list[str] | None = Query(default=None),
    assignee_id: str | None = Query(default=None, alias="assigneeId"),
    due: DUE_FILTER = "all",
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    project = get_project_or_404(store, project_id)
    require_member(store, project, user)

    term = (search or "").strip().lower()
    cards = store.list_cards(project["id"])
    if term:
        cards = [
            c
            for c in cards
            if term
            in " ".join([c["title"], c["description"], " ".join(c["labels"])]).lower()
        ]
    if priorities:
        valid = [p for p in priorities if p in _VALID_PRIORITIES]
        cards = [c for c in cards if c["priority"] in set(valid)]
    if assignee_id:
        cards = [c for c in cards if c["assigneeId"] == assignee_id]

    today = datetime.date.today()
    week_end = today + datetime.timedelta(days=7)

    def _due_matches(c: dict) -> bool:
        d = c["dueDate"]
        if due == "all":
            return True
        if due == "no-date":
            return d is None
        if d is None:
            return False
        if due == "overdue":
            return d < today
        if due == "this-week":
            return today <= d <= week_end
        return True

    cards = [c for c in cards if _due_matches(c)]
    cards.sort(key=lambda c: (c.get("position", 0), c["id"]))

    comment_ids = {c["id"] for c in cards}
    comments = store.list_comments_for_cards(comment_ids)

    return {
        "project": store.project_to_dict(project),
        "columns": store.list_columns(project["id"]),
        "cards": [store.card_to_dict(c) for c in cards],
        "comments": comments,
        "members": store.list_members(project),
    }