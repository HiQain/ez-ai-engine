"""Keep ez's local copy of the price-book codes in sync with Laravel.

Laravel is the source of truth. ez periodically asks Laravel "which codes changed
since the last time I checked?" (GET /api/internal/codes/changed?since=...), then:
  - upserts each changed code into ez's `codes` table,
  - deletes any code Laravel reports as soft-deleted,
  - advances the cursor (the newest Laravel updated_at seen).

The cursor lives in the single `code_sync_state` row, so each run only fetches
what changed. Webhooks can be added later without changing this cursor model.
"""

from __future__ import annotations
from datetime import UTC, datetime
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.code import Code, CodeSyncState

_EPOCH = datetime(1970, 1, 1)
_SYNC_STATE_ID = 1
_MAX_PAGES = 1000  # safety cap so a bad cursor can never loop forever


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO8601 string (with 'Z' or offset) to naive UTC, matching the DB."""
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _get_state(db: Session) -> CodeSyncState:
    state = db.get(CodeSyncState, _SYNC_STATE_ID)
    if state is None:
        state = CodeSyncState(id=_SYNC_STATE_ID, last_updated_at=_EPOCH)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def sync_codes(db: Session) -> dict:
    """Run one full sync (paging until caught up). Returns a small summary."""
    state = _get_state(db)
    cursor = state.last_updated_at or _EPOCH
    newest = cursor

    base = settings.laravel_api_url.rstrip("/")
    url = f"{base}/api/internal/codes/changed"
    headers = {"X-Engine-Key": settings.engine_api_key or ""}

    upserts = 0
    deletes = 0

    with httpx.Client(timeout=30.0) as client:
        for _ in range(_MAX_PAGES):
            resp = client.get(
                url,
                headers=headers,
                params={"since": cursor.isoformat(), "limit": settings.code_sync_page_size},
            )
            resp.raise_for_status()
            payload = resp.json()
            rows = payload.get("codes", [])

            for row in rows:
                updated = _parse_dt(row.get("updated_at")) or _EPOCH
                newest = max(newest, updated)

                if row.get("deleted_at"):
                    existing = db.get(Code, row["id"])
                    if existing is not None:
                        db.delete(existing)
                        deletes += 1
                    continue

                _upsert_code(db, row)
                upserts += 1

            db.commit()

            if not payload.get("has_more"):
                break
            # Advance the cursor; stop if it can't move (all rows share a timestamp).
            if newest <= cursor:
                break
            cursor = newest

    state.last_updated_at = newest
    state.last_run_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()

    return {"upserts": upserts, "deletes": deletes, "cursor": newest.isoformat()}


def _upsert_code(db: Session, row: dict) -> None:
    code = db.get(Code, row["id"])
    if code is None:
        code = Code(id=row["id"])
        db.add(code)

    code.company_id = row.get("company_id")
    code.code_name = row.get("code_name")
    code.product_name = row.get("product_name")
    code.unit_of_measure = row.get("unit_of_measure")
    code.labor_cost = row.get("labor_cost")
    code.material_cost = row.get("material_cost")
    code.misc_cost = row.get("misc_cost")
    code.description = row.get("description")
    code.supplier_id = row.get("supplier_id")
    code.product_group_id = row.get("product_group_id")
    code.source_updated_at = _parse_dt(row.get("updated_at"))
