import base64
import hashlib
import hmac
import os
from typing import Annotated

from fastapi import Depends, Request, Response
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.models import User

SESSION_COOKIE = "session"
PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=PBKDF2_ITERATIONS,
        salt=base64.b64encode(salt).decode("ascii"),
        digest=base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_raw.encode("ascii"))
        expected = base64.b64decode(digest_raw.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations_raw))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().app_secret_key, salt="session")


def bootstrap_user(db: Session) -> None:
    if db.query(User).first() is not None:
        return
    settings = get_settings()
    user = User(username=settings.app_username, password_hash=hash_password(settings.app_password))
    db.add(user)
    db.commit()


def issue_session(response: Response, user: User) -> None:
    token = serializer().dumps({"user_id": user.id})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise AppError("unauthenticated", "Login required", 401)
    try:
        payload = serializer().loads(token)
    except BadSignature as exc:
        raise AppError("unauthenticated", "Invalid session", 401) from exc
    user = db.get(User, payload.get("user_id"))
    if user is None:
        raise AppError("unauthenticated", "Invalid session", 401)
    return user
