from fastapi import APIRouter, Depends

from ..models import User
from ..store import Store
from ..auth import get_current_user
from ._helpers import get_store

router = APIRouter(tags=["users"])


@router.get("/me", response_model=User)
def get_me(
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    return store.user_to_dict(user)