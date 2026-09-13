from fastapi import APIRouter, Depends, HTTPException, Query

from ..models import SearchResult
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_store

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchResult])
def search(
    q: str = Query(min_length=1),
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[dict]:
    if not q.strip():
        raise HTTPException(status_code=422, detail="Empty query")
    return store.search(user["id"], q)