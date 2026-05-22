# Frontend Architecture

The frontend lives under `frontend/src` and is a React + Vite + TypeScript app.

## Main responsibilities

- Authenticate with backend session cookie.
- Render a macOS Finder-like window.
- Load and display directory entries.
- Manage navigation history, selected paths, view mode, search query, dialogs, and context menus.
- Call backend APIs through a single API client.

## Key files

- `App.tsx` — top-level authenticated app state and operation wiring.
- `api.ts` — HTTP client and typed API wrappers.
- `types.ts` — shared frontend types for file entries and view modes.
- `selection.ts` — selection model helpers used by file views.
- `components/AppShell.tsx` — desktop background and Finder-like window.
- `components/Sidebar.tsx` — locations, favorites, recent paths.
- `components/Toolbar.tsx` — navigation, search, upload, new folder, view switch.
- `components/FileArea.tsx` — icon/list rendering, selection, drag-to-move.
- `components/ContextMenu.tsx` — right-click actions.
- `components/Dialogs.tsx` — rename, delete confirmation, details.
- `components/UploadPanel.tsx` — file upload panel.
- `styles.css` — Sonoma-inspired visual system.

## Selection model

Keep selection behavior in `selection.ts` rather than duplicating it in UI components. Existing tests cover toggle selection and inclusive range selection.

## API boundary

Only `api.ts` should know raw endpoint URLs and backend snake_case payload fields. Components should call semantic functions such as `api.rename(path, newName)`.
