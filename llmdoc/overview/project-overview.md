# Project Overview

Personal File Manager is a single-user web application for managing files on a Linux host. It provides a modern macOS Finder-like browser UI while operating on a real directory mounted into the backend.

## Core capabilities

- Login as the single configured user.
- Browse a configured file root.
- Switch between icon and list views.
- Create folders.
- Upload files with conflict detection.
- Download files.
- Rename, move, copy, and delete items.
- Delete to app-managed trash rather than permanent deletion.
- Search file and folder names from the current directory downward.
- Use multi-select, range selection, right-click context menu, and drag-to-move.
- Store favorites, recent paths, view preferences, operation logs, and trash records in SQLite.

## Non-goals in the current version

- Multi-user accounts.
- Public share links.
- Complex permissions.
- Desktop sync clients.
- Online Office editing.
- File version history.
- Chunked uploads.
- File content search.
- Heavy preview or transcoding pipelines.
- Trash restore UI.

## Main technology choices

- Backend: FastAPI, SQLAlchemy, SQLite.
- Frontend: React, Vite, TypeScript, lucide-react icons.
- Deployment: single Docker Compose service.
