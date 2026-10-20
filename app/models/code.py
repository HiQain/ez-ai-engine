"""ez's local copy of Laravel's price-book codes.

Laravel owns the codes (users create/edit/delete them there). ez keeps a mirror
in its own MySQL so matching can run here without calling Laravel per item. The
mirror is kept fresh by polling — see app/services/code_sync_service.py.

The primary key `id` is the SAME value as Laravel's `codes.id`, so an update or
delete on one side maps cleanly to the same row here.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Code(Base):
    __tablename__ = "codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    company_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    code_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_of_measure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    labor_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    material_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    misc_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Laravel's updated_at for this code — the sync cursor is based on it.
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=_utc_now, onupdate=_utc_now
    )


class CodeSyncState(Base):
    """Single-row bookmark (id=1): the newest Laravel updated_at ez has pulled."""

    __tablename__ = "code_sync_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
