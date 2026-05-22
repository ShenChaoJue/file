# Security Boundaries

These rules are mandatory for changes involving auth, file paths, filesystem operations, upload/download, metadata paths, or deployment.

## Root directory sandbox

All managed files must stay under `FILES_ROOT`. User input paths are root-relative paths such as `/Photos/cat.jpg`; they are not host absolute paths.

`backend/app/filesystem.py` is the root-boundary authority. Do not perform raw path resolution or file mutations from routers or metadata helpers.

Required behavior:

- Resolve paths canonically before use.
- Reject `../` traversal.
- Reject access outside `FILES_ROOT`.
- Reject symlink escapes outside `FILES_ROOT`.
- Validate new names so they are a single path segment, not a path.
- Store metadata paths as root-relative paths where possible.

## File operations

Supported file mutations should go through `FileSystemService`:

- create folder
- rename
- move
- copy
- delete to trash
- upload target validation
- download target validation
- search base validation

Delete operations must move files to app-managed trash under `APP_DATA_DIR/trash`; they must not permanently delete managed files in first-version behavior.

## Auth

The app is single-user. The first user is created from `APP_USERNAME` and `APP_PASSWORD` only when no user exists. Later environment changes must not overwrite the existing password hash.

Sessions use a signed HTTP-only cookie named `session`. If changing deployment to HTTPS-only production, revisit the cookie `secure` setting.

## Tests to run after security-sensitive changes

```bash
cd backend
python -m pytest tests/test_filesystem_security.py tests/test_files_api.py tests/test_auth.py -v
```
