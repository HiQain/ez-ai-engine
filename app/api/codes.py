"""Manual + read endpoints for the mirrored price-book codes.

- POST /internal/codes/sync  → run a sync right now (testing / on-demand refresh)
- GET  /internal/codes       → quick count, to confirm the mirror is populated

Both require the engine key, like the rest of the internal surface.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_engine_key
from app.models.code import Code, CodeSyncState
from app.services.code_sync_service import sync_codes

router = APIRouter(
    prefix="/internal/codes",
    tags=["Codes"],
    dependencies=[Depends(require_engine_key)],
)


@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)) -> dict:
    return sync_codes(db)


@router.get("")
def codes_summary(db: Session = Depends(get_db)) -> dict:
    total = db.scalar(select(func.count()).select_from(Code)) or 0
    state = db.get(CodeSyncState, 1)
    return {
        "total": int(total),
        "last_synced_at": state.last_run_at.isoformat() if state and state.last_run_at else None,
        "cursor": state.last_updated_at.isoformat() if state and state.last_updated_at else None,
    }
