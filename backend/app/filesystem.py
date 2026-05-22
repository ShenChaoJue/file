import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.errors import AppError
from app.schemas import FileEntry


@dataclass(frozen=True)
class TrashMove:
    original_path: str
    trash_path: str
    original_name: str


class FileSystemService:
    def __init__(self, root: Path, app_data_dir: Path) -> None:
        self.root = root.resolve()
        self.app_data_dir = app_data_dir.resolve()
        self.trash_dir = self.app_data_dir / "trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def to_relative(self, absolute: Path) -> str:
        rel = absolute.resolve().relative_to(self.root)
        rel_text = rel.as_posix()
        return "/" if rel_text == "." else f"/{rel_text}"

    def resolve(self, user_path: str, *, must_exist: bool = True) -> Path:
        if not user_path.startswith("/"):
            user_path = f"/{user_path}"
        raw = user_path.lstrip("/")
        candidate = (self.root / raw).resolve(strict=False)
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise AppError("path_outside_root", "Path is outside the managed root", 403) from exc
        if must_exist and not candidate.exists():
            raise AppError("path_not_found", "Path does not exist", 404)
        if must_exist:
            real = candidate.resolve()
            try:
                real.relative_to(self.root)
            except ValueError as exc:
                raise AppError("path_outside_root", "Path is outside the managed root", 403) from exc
        return candidate

    def validate_name(self, name: str) -> str:
        clean = name.strip()
        if not clean or clean in {".", ".."} or "/" in clean or "\\" in clean:
            raise AppError("invalid_name", "Invalid file name", 400)
        return clean

    def entry_for(self, path: Path) -> FileEntry:
        stat = path.lstat()
        if path.is_symlink():
            kind = "symlink"
        elif path.is_dir():
            kind = "directory"
        elif path.is_file():
            kind = "file"
        else:
            kind = "other"
        return FileEntry(
            name=path.name,
            path=self.to_relative(path),
            kind=kind,
            size=None if kind == "directory" else stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            can_download=kind == "file",
        )

    def list_dir(self, user_path: str) -> list[FileEntry]:
        directory = self.resolve(user_path)
        if not directory.is_dir():
            raise AppError("not_directory", "Path is not a directory", 400)
        return sorted((self.entry_for(child) for child in directory.iterdir()), key=lambda item: (item.kind != "directory", item.name.lower()))

    def create_folder(self, parent_path: str, name: str) -> FileEntry:
        parent = self.resolve(parent_path)
        if not parent.is_dir():
            raise AppError("not_directory", "Parent is not a directory", 400)
        target = parent / self.validate_name(name)
        self.resolve(self.to_relative_for_candidate(target), must_exist=False)
        if target.exists():
            raise AppError("target_exists", "Target already exists", 409)
        target.mkdir()
        return self.entry_for(target)

    def rename(self, user_path: str, new_name: str) -> FileEntry:
        source = self.resolve(user_path)
        target = source.parent / self.validate_name(new_name)
        self.resolve(self.to_relative_for_candidate(target), must_exist=False)
        if target.exists():
            raise AppError("target_exists", "Target already exists", 409)
        source.rename(target)
        return self.entry_for(target)

    def move_many(self, sources: list[str], target_dir: str) -> list[FileEntry]:
        target = self.resolve(target_dir)
        if not target.is_dir():
            raise AppError("not_directory", "Target is not a directory", 400)
        moved: list[FileEntry] = []
        for source_path in sources:
            source = self.resolve(source_path)
            destination = target / source.name
            self.resolve(self.to_relative_for_candidate(destination), must_exist=False)
            if destination.exists():
                raise AppError("target_exists", "Target already exists", 409)
            source.rename(destination)
            moved.append(self.entry_for(destination))
        return moved

    def copy_many(self, sources: list[str], target_dir: str) -> list[FileEntry]:
        target = self.resolve(target_dir)
        if not target.is_dir():
            raise AppError("not_directory", "Target is not a directory", 400)
        copied: list[FileEntry] = []
        for source_path in sources:
            source = self.resolve(source_path)
            destination = target / source.name
            self.resolve(self.to_relative_for_candidate(destination), must_exist=False)
            if destination.exists():
                raise AppError("target_exists", "Target already exists", 409)
            if source.is_dir():
                shutil.copytree(source, destination, symlinks=True)
            else:
                shutil.copy2(source, destination)
            copied.append(self.entry_for(destination))
        return copied

    def delete_to_trash(self, user_path: str) -> TrashMove:
        source = self.resolve(user_path)
        original_path = self.to_relative(source)
        trash_name = f"{uuid.uuid4().hex}-{source.name}"
        destination = self.trash_dir / trash_name
        shutil.move(str(source), destination)
        return TrashMove(original_path=original_path, trash_path=str(destination), original_name=source.name)

    def to_relative_for_candidate(self, candidate: Path) -> str:
        try:
            rel = candidate.resolve(strict=False).relative_to(self.root)
        except ValueError as exc:
            raise AppError("path_outside_root", "Path is outside the managed root", 403) from exc
        rel_text = rel.as_posix()
        return "/" if rel_text == "." else f"/{rel_text}"
