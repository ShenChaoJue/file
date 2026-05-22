from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import clear_session, current_user, issue_session, verify_password
from app.db import get_db
from app.errors import AppError
from app.models import User
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("invalid_credentials", "Invalid username or password", 401)
    issue_session(response, user)
    return LoginResponse(username=user.username)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    clear_session(response)
    return {"status": "ok"}


@router.get("/me", response_model=LoginResponse)
def me(user: Annotated[User, Depends(current_user)]) -> LoginResponse:
    return LoginResponse(username=user.username)
