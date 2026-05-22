# Personal File Manager Design

Date: 2026-05-22
Status: Approved for implementation planning

## Goal

Build a single-user personal file management system for Linux, delivered as a web application. The app manages a configured real directory on the host machine while storing application metadata in SQLite. The user experience should resemble modern macOS Sonoma Finder: a polished windowed layout, translucent sidebar, compact toolbar, icon and list views, contextual actions, drag and drop, and multi-selection.

## Non-Goals

The first version will not include multi-user accounts, public share links, complex permission models, desktop sync clients, online Office editing, file version history, or heavy preview/transcoding pipelines. These can be considered later after the core file manager is stable.

## Product Scope

The first version includes:

- Single-user login, with the initial account created from deployment environment variables.
- Browsing a configured root directory, such as `/data/files` inside the container.
- Icon and list view modes.
- Back/forward navigation, path navigation, search, upload, and new-folder actions.
- File and folder operations: upload, download, rename, delete, move, copy, and create folder.
- Multi-select, right-click context menu, and drag-to-move interactions.
- Sidebar sections for common locations, favorites, and recent access.
- Metadata persistence for favorites, recent paths, view preferences, and operation logs.
- Basic filename search within the managed root directory.

## Architecture

The application uses a standard extensible structure while keeping deployment simple.

### Frontend

The frontend is React, Vite, and TypeScript. It owns the Finder-style interface, selection behavior, context menus, drag and drop, upload progress, dialogs, and view switching.

### Backend

The backend is FastAPI. It exposes API endpoints for authentication, directory listing, file operations, uploads, search, favorites, recent access, preferences, and operation logs.

### Database

SQLite stores application metadata:

- Single-user account and password hash.
- Session or token state if server-side session tracking is used.
- Favorite paths.
- Recent paths.
- Per-path or global view preferences.
- Operation logs.

### File Storage

Files remain on the Linux host filesystem. Docker Compose mounts a host directory, for example `/srv/personal-files`, into the container as `/data/files`. The backend treats this mount as the only managed root.

### Deployment

Docker Compose starts one application service. The frontend is built into static assets and served by the FastAPI application, so the first version does not require separate Nginx, Redis, worker, or database containers. SQLite data is stored on a persistent Docker volume or bind mount.

## Security Boundary

The root directory sandbox is the most important backend rule. Every user-provided path must be resolved to a canonical real path and checked to ensure it remains inside the configured root directory. This applies to listing, download, upload, rename, copy, move, delete, search, and metadata operations.

The implementation must reject path traversal attempts, absolute paths outside the root, encoded traversal, and symlink escapes. Symlink handling should be conservative: operations may show symlinks, but following a symlink outside the root must be blocked.

Deletion should move items into an application-managed trash directory in app data, separate from the managed file root. The trash record should preserve the original relative path, original name, and deletion time. The first version does not need a full restore UI, but delete operations must not immediately remove files permanently.

## Backend Components

### Auth

Handles single-user login, password hashing, and authenticated API access. The initial username and password come from deployment environment variables such as `APP_USERNAME` and `APP_PASSWORD`. On first startup, the backend creates the user in SQLite if no user exists. If a user already exists, startup must not overwrite the stored password hash. The first version should avoid registration flows and admin panels.

### Filesystem

Owns path resolution, root-boundary validation, directory reads, new folder creation, rename, move, copy, delete-to-trash, and download preparation. Other modules should not perform raw file operations directly.

### Metadata

Owns favorites, recent access, view preferences, and operation logs. It stores paths relative to the managed root where possible, so deployment paths can change without corrupting metadata.

### Upload

Handles regular multipart uploads. Chunked uploads are out of scope for the first version. If an upload target already exists, the backend returns a structured conflict response and the frontend asks the user before overwriting or renaming.

### Search

Performs basic filename search from the current directory downward. The first version searches file and folder names only, not file contents. Global root-wide search can be added later as a separate mode. Search must enforce limits on scan depth, total visited entries, and response size so large directories do not block the service indefinitely.

## Frontend Components

### AppShell

Provides the full-screen desktop background and main Finder-like window. It owns high-level layout and authenticated state.

### Sidebar

Shows common locations, favorites, and recent paths. Selecting an item navigates the file area to that path.

### Toolbar

Contains back, forward, path navigation, search, view toggle, upload, and new folder controls. Controls should use icons where appropriate and maintain compact macOS-like density.

### FileArea

Renders the current directory in icon view or list view. It receives file entries from API state and delegates selection behavior to a dedicated selection model.

### ContextMenu

Provides right-click actions such as open folder, download file, rename, copy, move, delete, and show details. Available actions depend on current selection. `Show details` is limited to metadata such as size, type, modified time, and relative path; content preview is out of scope for the first version.

### Dialogs And Panels

Rename, confirmation, conflict, and upload panels provide focused feedback for file operations. Destructive and overwriting actions require explicit confirmation.

### SelectionModel

Centralizes single selection, range selection, multi-selection, keyboard selection, and drag selection. This keeps selection behavior consistent between icon and list views.

## Data Flow

A typical directory read follows this flow:

1. The frontend requests `GET /api/files?path=/photos`.
2. The backend resolves `/photos` relative to the configured root.
3. The filesystem module verifies the resolved path remains inside the root.
4. The backend reads the directory and returns entries with names, relative paths, type, size, modified time, and basic capability flags.
5. The frontend renders entries in the active view and records recent access through metadata.

A typical file operation follows this flow:

1. The user chooses an action from the toolbar, context menu, keyboard shortcut, or drag interaction.
2. The frontend sends a structured API request using root-relative paths.
3. The backend validates all source and target paths against the root sandbox.
4. The filesystem module performs the operation.
5. Metadata records the operation when appropriate.
6. The frontend refreshes the current directory and shows success or error feedback.

## Error Handling

The backend returns structured errors with stable codes and human-readable messages. Important cases include:

- Unauthenticated request.
- Path not found.
- Path outside managed root.
- Permission denied by the OS.
- Target already exists.
- Invalid name.
- Directory not empty where relevant.
- File too large for configured upload limits.
- Search limit exceeded.
- Root directory unavailable.

The frontend should present these as concise file-manager-style messages. Technical details can be logged in the backend, but the UI should stay calm and actionable.

## Testing Strategy

Testing focuses on the highest-risk behavior.

### Backend Tests

- Path safety tests for `../`, absolute paths, encoded traversal, and symlink escape attempts.
- File operation tests for create folder, rename, move, copy, delete-to-trash, and conflict cases.
- API tests for login, directory listing, upload, search, favorites, recent access, and preferences.
- Search limit tests for depth, scanned entry count, and response size.

### Frontend Tests

- View switching between icon and list mode.
- Multi-select and range-select behavior.
- Context menu actions for single and multiple selections.
- Drag-to-move flow.
- Upload progress and conflict handling.
- Error display for common backend error codes.

### Deployment Verification

- `docker compose up` starts the app service.
- `APP_USERNAME` and `APP_PASSWORD` create the initial user on first startup without overwriting an existing user.
- The configured host file directory is readable and writable from the app.
- SQLite metadata persists across container restarts.
- The built frontend is served by the backend.

## Acceptance Criteria

The first version is complete when a user can deploy the app on Linux with Docker Compose, open it in a browser, log in as the configured single user, and manage files under the mounted root directory with a modern macOS Finder-like interface. The user must be able to browse, upload, download, rename, delete to app-managed trash, move, copy, create folders, search by filename from the current directory, switch between icon and list views, use multi-select, use a right-click context menu, and drag items to move them without escaping the configured root directory.
