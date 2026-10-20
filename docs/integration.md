# ez — AI Takeoff Engine: Integration Guide (for the Laravel API)

This service (`ez`) is the internal AI engine. The Laravel API
(`api.ezestimater.com`) is the gateway: it authenticates end users, owns the
estimates/billing data, and **calls this service** for the AI takeoff work.
End users never talk to `ez` directly.

```
Mobile/Web ──(Sanctum auth)──> Laravel API ──(HTTP + X-Engine-Key)──> ez (FastAPI)
```

## Base URL & ports

- `ez` runs on **:8000** (FastAPI/uvicorn). This port does not change.
- Laravel's dev server must therefore run on a **different** port (e.g. `php artisan serve --port=8001`), because both default to 8000.
- Dev base URL for Laravel to call: `http://127.0.0.1:8000`
- Production: put `ez` on a private hostname only Laravel can reach; never expose it publicly.

Interactive API schema (source of truth for exact request/response shapes):
`http://127.0.0.1:8000/docs` (Swagger) and `/openapi.json`.

## Authentication

Every `/takeoff/*` request must include a shared-secret header:

```
X-Engine-Key: <the ENGINE_API_KEY value>
```

- The secret lives in `ez`'s `.env` as `ENGINE_API_KEY`. Laravel must store the
  same value (e.g. its own `.env`) and send it on every call.
- Missing/wrong key → `401`. The health root `GET /` is open (no key needed).
- If `ENGINE_API_KEY` is unset, auth is off in dev/test but **refused in
  production** (returns `503`), so production must set it.

Example from Laravel:

```php
$res = Http::withHeaders(['X-Engine-Key' => config('services.ez.key')])
    ->baseUrl(config('services.ez.url'))
    ->attach('file', $pdfContents, $fileName)
    ->post('/takeoff/upload');
```

## Endpoints

All paths are prefixed with `/takeoff` and require the `X-Engine-Key` header.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/takeoff/upload` | Multipart `file` (PDF/PNG/JPG). Returns `{ takeoff_id, file_name, status }`. |
| GET | `/takeoff/{job_id}` | Job status: `{ id, file_name, status }`. **Poll this** for progress. |
| POST | `/takeoff/{job_id}/analyze?force=false` | Starts AI analysis on the Celery worker and returns immediately (`status: "processing"`). `force=true` reruns and replaces items. |
| GET | `/takeoff/{job_id}/items` | The extracted takeoff line items. |
| POST | `/takeoff/{job_id}/items` | Add an item. |
| PATCH | `/takeoff/{job_id}/items/{item_id}` | Edit an item. |
| DELETE | `/takeoff/{job_id}/items/{item_id}` | Remove an item. |
| POST | `/takeoff/{job_id}/match` | Match items to catalog products. |
| POST | `/takeoff/{job_id}/estimate` | Build the estimate from matched items. |
| GET | `/takeoff/{job_id}/estimate` | Fetch the generated estimate. |

## Typical flow (Laravel orchestrates)

1. `POST /takeoff/upload` → store the returned `takeoff_id` in `ezestimater_pd`,
   linked to the user/estimate.
2. `POST /takeoff/{id}/analyze` → returns `processing` right away.
3. **Poll** `GET /takeoff/{id}` until `status == "completed"` (analysis runs in
   the background worker).
4. `GET /takeoff/{id}/items` → review/let the user edit via the item endpoints.
5. `POST /takeoff/{id}/match` then `POST /takeoff/{id}/estimate`.
6. Write the final estimate into Laravel's own tables.

## Status values

`uploaded` → `processing` → `completed` (or `failed`). Treat `processing` as
"keep polling"; a second `analyze` on an already-processing job returns `409`.

## Linking the two databases

`ez` keeps its working data in the `ez` database; Laravel keeps the system of
record in `ezestimater_pd`. The only thing that crosses the wire is the
`takeoff_id`. Store a mapping (e.g. `estimate_id ↔ takeoff_id`) on the Laravel
side. Neither database should read or write the other's tables.

## Prerequisites for `ez` to run

- MySQL database `ez`, Redis (broker on `:6380`), and a Celery worker:
  `celery -A app.core.celery_app worker` (so `analyze` jobs actually run).
- See `.env.example` for all required configuration.
