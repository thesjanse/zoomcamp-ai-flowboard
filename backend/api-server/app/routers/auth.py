from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import Request

from ..models import (
    AuthResponse,
    ChangeEmailInput,
    ChangePasswordInput,
    LoginInput,
    RegisterInput,
    User,
)
from ..store import Store
from ..auth import (
    create_token,
    get_current_user,
    hash_password,
    revoke_token,
    verify_password,
)
from ._helpers import get_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    payload: RegisterInput,
    request: Request,
    store: Store = Depends(get_store),
) -> AuthResponse:
    if store.get_user_by_email(payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = store.create_user(payload.name, payload.email, hash_password(payload.password))
    token = create_token(user["id"])
    return AuthResponse(token=token, user=store.user_to_dict(user))


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginInput,
    store: Store = Depends(get_store),
) -> AuthResponse:
    user = store.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"])
    return AuthResponse(token=token, user=store.user_to_dict(user))


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    user: dict = Depends(get_current_user),
) -> Response:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        revoke_token(auth_header.split(" ", 1)[1].strip())
    return Response(status_code=204)


@router.patch("/email", response_model=User)
def change_email(
    payload: ChangeEmailInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> dict:
    if store.get_user_by_email(payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email already in use")
    user = store.update_user_email(user, payload.email)
    return store.user_to_dict(user)


@router.patch("/password", status_code=204)
def change_password(
    payload: ChangePasswordInput,
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    if not verify_password(payload.currentPassword, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    store.update_user_password(user, hash_password(payload.newPassword))
    return Response(status_code=204)


@router.delete("/account", status_code=204)
def delete_account(
    user: dict = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> Response:
    if store.user_admins_any(user):
        raise HTTPException(
            status_code=409, detail="Projects still need to be transferred"
        )
    store.delete_user(user)
    return Response(status_code=204)