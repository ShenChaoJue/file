from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.metadata import add_favorite, get_preferences, list_favorites, list_recent, remove_favorite, set_preference, touch_recent
from app.models import User
from app.schemas import FavoriteRequest, PreferenceRequest

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


def path_list(paths: list[str]) -> list[dict[str, str]]:
    return [{"path": path} for path in paths]


@router.get("/favorites")
def favorites(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, str]]:
    return path_list(list_favorites(db))


@router.post("/favorites")
def create_favorite(payload: FavoriteRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    add_favorite(db, payload.path)
    return {"status": "ok"}


@router.delete("/favorites")
def delete_favorite(path: str, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    remove_favorite(db, path)
    return {"status": "ok"}


@router.get("/recent")
def recent(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, str]]:
    return path_list(list_recent(db))


@router.post("/recent")
def create_recent(payload: FavoriteRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    touch_recent(db, payload.path)
    return {"status": "ok"}


@router.get("/preferences")
def preferences(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    return get_preferences(db)


@router.put("/preferences")
def update_preference(payload: PreferenceRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    set_preference(db, payload.key, payload.value)
    return {"status": "ok"}
