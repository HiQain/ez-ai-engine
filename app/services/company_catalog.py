"""Build the product-matching catalog from ez's synced `codes` table.

Previously the matcher used the global catalog pulled from admin.ezestimater.com
(all companies, no scoping). This instead uses the codes ez keeps in sync from
Laravel (see code_sync_service), filtered to one company — so matching is
company-specific.

Because the synced `codes.id` IS Laravel's `codes.id`, a match's product_id is
directly usable as Laravel's `takeoff_items.code_id` — no id translation needed.
"""

from sqlalchemy.orm import Session
from app.models.code import Code
from app.schemas.matching import CatalogProduct


def get_company_catalog(db: Session, company_id: int | None) -> list[CatalogProduct]:
    query = db.query(Code)
    if company_id is not None:
        query = query.filter(Code.company_id == company_id)

    products: list[CatalogProduct] = []
    for code in query.all():
        if not code.code_name:
            # The matcher keys on code_name; skip rows that have none.
            continue
        products.append(
            CatalogProduct(
                id=code.id,
                code_name=code.code_name,
                product_name=code.product_name,
                description=code.description or "",
                unit_of_measure=code.unit_of_measure,
                labor_cost=code.labor_cost,
                material_cost=code.material_cost,
                misc_cost=code.misc_cost,
            )
        )
    return products
