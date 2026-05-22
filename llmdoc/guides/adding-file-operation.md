# Adding A File Operation

Use this guide when adding a new file mutation or expanding an existing one.

## Required steps

1. Add or extend a test in `backend/tests/` that describes the behavior.
2. Route all path handling through `FileSystemService`.
3. Return or persist root-relative paths only.
4. Add or extend the API route under `backend/app/routers/files.py`.
5. Update `frontend/src/api.ts` if the UI needs the new operation.
6. Wire the action into `frontend/src/App.tsx` or a component.
7. Run backend tests and frontend build.

## Never skip

- Root-boundary checks.
- Name validation.
- Conflict handling for targets that already exist.
- Structured error codes.

## Example operation categories

- Directory creation
- Rename
- Move
- Copy
- Delete to trash
- Upload
- Download
- Search
