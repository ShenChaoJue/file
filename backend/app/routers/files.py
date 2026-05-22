import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.filesystem import FileSystemService
from app.models import OperationLog, TrashRecord, User
from app.schemas import DirectoryResponse, FileEntry, MoveCopyRequest, RenameRequest, SearchResponse

router = APIRouter(prefix="/api/files", tags=["files"])


def fs() -> FileSystemService:
    settings = get_settings()
    return FileSystemService(settings.files_root, settings.app_data_dir)


def log_operation(db: Session, action: str, source: str | None = None, target: str | None = None) -> None:
    db.add(OperationLog(action=action, source_path=source, target_path=target))
    db.commit()


@router.get("", response_model=DirectoryResponse)
def list_files(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    path: str = Query(default="/"),
) -> DirectoryResponse:
    entries = fs().list_dir(path)
    log_operation(db, "list", path)
    return DirectoryResponse(path=path, entries=entries)


@router.post("/folders", response_model=FileEntry)
def create_folder(
    payload: dict[str, str],
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileEntry:
    raw_path = payload.get("path", "")
    clean = raw_path.strip("/")
    parent, name = clean.rsplit("/", 1) if "/" in clean else ("/", clean)
    if not name:
        raise AppError("invalid_name", "Folder name is required", 400)
    entry = fs().create_folder(parent if parent.startswith("/") else f"/{parent}", name)
    log_operation(db, "create_folder", entry.path)
    return entry


@router.post("/rename", response_model=FileEntry)
def rename(payload: RenameRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> FileEntry:
    entry = fs().rename(payload.path, payload.new_name)
    log_operation(db, "rename", payload.path, entry.path)
    return entry


@router.post("/move", response_model=list[FileEntry])
def move(payload: MoveCopyRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[FileEntry]:
    entries = fs().move_many(payload.sources, payload.target_dir)
    log_operation(db, "move", ",".join(payload.sources), payload.target_dir)
    return entries


@router.post("/copy", response_model=list[FileEntry])
def copy(payload: MoveCopyRequest, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[FileEntry]:
    entries = fs().copy_many(payload.sources, payload.target_dir)
    log_operation(db, "copy", ",".join(payload.sources), payload.target_dir)
    return entries


@router.delete("")
def delete_file(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)], path: str = Query()) -> dict[str, str]:
    trash_move = fs().delete_to_trash(path)
    db.add(TrashRecord(original_path=trash_move.original_path, trash_path=trash_move.trash_path, original_name=trash_move.original_name))
    db.add(OperationLog(action="delete", source_path=trash_move.original_path, target_path=trash_move.trash_path))
    db.commit()
    return {"status": "ok"}


@router.post("/upload", response_model=FileEntry)
async def upload(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    path: str = Form(default="/"),
    file: UploadFile = File(),
) -> FileEntry:
    service = fs()
    directory = service.resolve(path)
    if not directory.is_dir():
        raise AppError("not_directory", "Upload target is not a directory", 400)
    name = service.validate_name(file.filename or "upload.bin")
    target = directory / name
    service.resolve(service.to_relative_for_candidate(target), must_exist=False)
    if target.exists():
        raise AppError("target_exists", "Target already exists", 409)
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    entry = service.entry_for(target)
    log_operation(db, "upload", None, entry.path)
    return entry


@router.get("/download")
def download(user: Annotated[User, Depends(current_user)], path: str = Query()) -> FileResponse:
    target = fs().resolve(path)
    if not target.is_file():
        raise AppError("not_file", "Path is not a downloadable file", 400)
    return FileResponse(target, filename=target.name)


@router.get("/search", response_model=SearchResponse)
def search(user: Annotated[User, Depends(current_user)], path: str = Query(default="/"), q: str = Query(min_length=1)) -> SearchResponse:
    settings = get_settings()
    service = fs()
    base = service.resolve(path)
    if not base.is_dir():
        raise AppError("not_directory", "Search base is not a directory", 400)
    results: list[FileEntry] = []
    visited = 0
    truncated = False
    needle = q.lower()
    stack: list[tuple[Path, int]] = [(base, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > settings.search_max_depth:
            truncated = True
            continue
        for child in current.iterdir():
            visited += 1
            if visited > settings.search_max_entries:
                truncated = True
                stack.clear()
                break
            if needle in child.name.lower():
                results.append(service.entry_for(child))
                if len(results) >= settings.search_max_results:
                    truncated = True
                    stack.clear()
                    break
            if child.is_dir() and not child.is_symlink():
                stack.append((child, depth + 1))
    results.sort(key=lambda entry: entry.path.lower())
    return SearchResponse(query=q, base_path=path, entries=results, truncated=truncated)
