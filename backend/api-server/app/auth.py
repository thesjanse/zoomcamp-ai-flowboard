"""Password hashing, bearer-token issuing, and the current-user dependency.

Passwords are hashed with salted PBKDF2-HMAC-SHA256 (stdlib only). Auth tokens
are signed JWTs (HS256); logout adds the token's ``jti`` to an in-memory
denylist so revocation works within the server's lifetime.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config

_HASH_ALGO = "pbkdf2_sha256"
_PBKDF2_ROUNDS = 390_000
_SALT_BYTES = 16

_DELETED_USER_NAME = "Deleted user"

_bearer = HTTPBearer(auto_error=False)
_revoked: set[tuple[str, int]] = set()  # (jti, exp) of logged-out tokens


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS
    )
    return f"{_HASH_ALGO}${_PBKDF2_ROUNDS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_s, salt_hex, hash_hex = stored.split("$", 3)
    except ValueError:
        return False
    if algo != _HASH_ALGO:
        return False
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds_s)
    )
    return hmac.compare_digest(derived.hex(), hash_hex)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


def create_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + config.TOKEN_EXPIRE_DAYS * 86_400,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None


def revoke_token(token: str) -> None:
    payload = decode_token(token)
    if payload is None:
        return
    _revoked.add((payload["jti"], int(payload["exp"] or 0)))
    _prune_revoked()


def _prune_revoked() -> None:
    now = int(time.time())
    _revoked.difference_update(
        (jti, exp) for (jti, exp) in _revoked if exp < now
    )


def _is_revoked(payload: dict) -> bool:
    return (payload["jti"], int(payload["exp"] or 0)) in _revoked


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Resolve the authenticated user from the Authorization header."""
    token = credentials.credentials if credentials is not None else None
    if token is None:
        raise _unauthorized()

    payload = decode_token(token)
    if payload is None or _is_revoked(payload):
        raise _unauthorized()

    store = request.app.state.store
    user = store.get_user(payload.get("sub"))
    if user is None:
        raise _unauthorized()
    return user