"""FastAPI application entry-point."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .models import ErrorResponse
from .store import Store


def _error_response(
    status: int, detail: str | None, errors: dict | None = None
) -> JSONResponse:
    body = ErrorResponse(
        title=str(status), detail=detail, status=status, errors=errors
    )
    return JSONResponse(
        status_code=status, content=body.model_dump(exclude_none=True)
    )


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="Api", version="0.1.0")
    app.state.store = store or Store(seed=True)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors: dict[str, list[str]] = {}
        for err in exc.errors():
            loc = err.get("loc", ())
            field_parts = [
                str(p)
                for p in loc
                if p not in ("body", "query", "path", "header", "cookie")
            ]
            field = ".".join(field_parts) if field_parts else "body"
            errors.setdefault(field, []).append(err.get("msg", "invalid"))
        return _error_response(422, "Validation Error", errors)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        response = _error_response(exc.status_code, str(exc.detail))
        if getattr(exc, "headers", None):
            for key, value in exc.headers.items():
                response.headers[key] = value
        return response

    @app.exception_handler(StarletteHTTPException)
    async def starlette_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(exc.status_code, str(exc.detail))

    from .routers import (
        auth_router,
        board_router,
        cards_router,
        columns_router,
        comments_router,
        health_router,
        invites_router,
        members_router,
        projects_router,
        relationships_router,
        search_router,
        users_router,
    )

    api_router = APIRouter(prefix="/api")
    for router in (
        health_router,
        auth_router,
        users_router,
        projects_router,
        board_router,
        columns_router,
        members_router,
        invites_router,
        cards_router,
        comments_router,
        relationships_router,
        search_router,
    ):
        api_router.include_router(router)
    app.include_router(api_router)

    return app


app = create_app()