# Configuration Reference

## Environment variables

- `APP_USERNAME` — initial login username.
- `APP_PASSWORD` — initial login password.
- `APP_SECRET_KEY` — signed session secret.
- `FILES_ROOT` — mounted host path to manage.
- `APP_DATA_DIR` — app data and trash directory.
- `DATABASE_URL` — optional SQLAlchemy URL override.
- `UPLOAD_MAX_BYTES` — optional upload size limit.
- `SEARCH_MAX_DEPTH` — recursive search depth cap.
- `SEARCH_MAX_ENTRIES` — visited entry cap for search.
- `SEARCH_MAX_RESULTS` — search result cap.

## Default container paths

- `/data/files` for managed files.
- `/app/data` for SQLite, trash, and runtime data.

## Important behavior

- The first user is created only if the users table is empty.
- Existing users are not overwritten by later environment changes.
- The session cookie name is `session`.
