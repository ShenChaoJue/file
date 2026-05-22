from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Favorite, Preference, RecentPath


def normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def add_favorite(db: Session, path: str) -> None:
    path = normalize_path(path)
    if db.query(Favorite).filter(Favorite.path == path).first() is None:
        db.add(Favorite(path=path))
        db.commit()


def remove_favorite(db: Session, path: str) -> None:
    path = normalize_path(path)
    favorite = db.query(Favorite).filter(Favorite.path == path).first()
    if favorite is not None:
        db.delete(favorite)
        db.commit()


def list_favorites(db: Session) -> list[str]:
    return [row.path for row in db.query(Favorite).order_by(Favorite.created_at.asc()).all()]


def touch_recent(db: Session, path: str) -> None:
    path = normalize_path(path)
    recent = db.query(RecentPath).filter(RecentPath.path == path).first()
    if recent is None:
        db.add(RecentPath(path=path, last_accessed_at=datetime.utcnow()))
    else:
        recent.last_accessed_at = datetime.utcnow()
    db.commit()


def list_recent(db: Session) -> list[str]:
    rows = db.query(RecentPath).order_by(RecentPath.last_accessed_at.desc()).limit(20).all()
    return [row.path for row in rows]


def set_preference(db: Session, key: str, value: str) -> None:
    pref = db.get(Preference, key)
    if pref is None:
        db.add(Preference(key=key, value=value))
    else:
        pref.value = value
    db.commit()


def get_preferences(db: Session) -> dict[str, str]:
    return {row.key: row.value for row in db.query(Preference).order_by(Preference.key.asc()).all()}
