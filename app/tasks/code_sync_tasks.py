"""Celery task that polls Laravel for code changes on a schedule.

Registered on the beat schedule in app/core/celery_app.py (every few minutes).
A thin shell around code_sync_service.sync_codes, so the logic stays testable
without a running broker.
"""

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.code_sync_service import sync_codes


@celery_app.task(name="codes.sync")
def sync_codes_task() -> dict:
    db = SessionLocal()
    try:
        return sync_codes(db)
    finally:
        db.close()
