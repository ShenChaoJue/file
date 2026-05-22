from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
class HealthResponse(BaseModel): status: str
class LoginRequest(BaseModel): username: str; password: str
class LoginResponse(BaseModel): username: str
class FileEntry(BaseModel):
    name: str; path: str; kind: Literal["file","directory","symlink","other"]; size: int|None; modified_at: datetime|None; can_download: bool
class DirectoryResponse(BaseModel): path: str; entries: list[FileEntry]
class RenameRequest(BaseModel): path: str; new_name: str
class MoveCopyRequest(BaseModel): sources: list[str] = Field(min_length=1); target_dir: str
class SearchResponse(BaseModel): query: str; base_path: str; entries: list[FileEntry]; truncated: bool
class FavoriteRequest(BaseModel): path: str
class PreferenceRequest(BaseModel): key: str; value: str
