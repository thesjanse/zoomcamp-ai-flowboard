from .auth import router as auth_router
from .board import router as board_router
from .cards import router as cards_router
from .columns import router as columns_router
from .comments import router as comments_router
from .health import router as health_router
from .invites import router as invites_router
from .members import router as members_router
from .projects import router as projects_router
from .relationships import router as relationships_router
from .search import router as search_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "board_router",
    "cards_router",
    "columns_router",
    "comments_router",
    "health_router",
    "invites_router",
    "members_router",
    "projects_router",
    "relationships_router",
    "search_router",
    "users_router",
]