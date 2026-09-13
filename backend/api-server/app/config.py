"""Application configuration.

Values come from environment variables so the app can be deployed, but the
defaults are safe for local development.
"""

from __future__ import annotations

import os

TOKEN_EXPIRE_DAYS = int(os.getenv("TOKEN_EXPIRE_DAYS", "30"))
INVITE_DEFAULT_DAYS = int(os.getenv("INVITE_DEFAULT_DAYS", "7"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"