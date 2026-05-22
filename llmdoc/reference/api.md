# API Reference

## Authentication

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Files

- `GET /api/files?path=/`
- `POST /api/files/folders`
- `POST /api/files/rename`
- `POST /api/files/move`
- `POST /api/files/copy`
- `DELETE /api/files?path=/path`
- `POST /api/files/upload`
- `GET /api/files/download?path=/path`
- `GET /api/files/search?path=/base&q=query`

## Metadata

- `GET /api/metadata/favorites`
- `POST /api/metadata/favorites`
- `DELETE /api/metadata/favorites?path=/path`
- `GET /api/metadata/recent`
- `POST /api/metadata/recent`
- `GET /api/metadata/preferences`
- `PUT /api/metadata/preferences`

## Common response shapes

Directory listing returns:

```json
{
  "path": "/",
  "entries": []
}
```

Errors return:

```json
{
  "error": {
    "code": "target_exists",
    "message": "Target already exists"
  }
}
```
