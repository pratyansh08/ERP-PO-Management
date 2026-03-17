import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.vendor import Vendor
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderDetailOut, PurchaseOrderOut

router = APIRouter(dependencies=[Depends(get_current_user)])

TAX_RATE = Decimal("0.05")
MONEY_PLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)

def _generate_reference_no(db: Session) -> str:
    # Simple, deterministic: PO-YYYY-000001 (based on DB id sequence)
    year = dt.datetime.utcnow().year
    next_id = (db.scalar(select(PurchaseOrder.id).order_by(PurchaseOrder.id.desc()).limit(1)) or 0) + 1
    return f"PO-{year}-{next_id:06d}"


@router.post("", response_model=PurchaseOrderDetailOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    try:
        vendor = db.get(Vendor, payload.vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        requested_product_ids = [i.product_id for i in payload.items]
        products = db.scalars(select(Product).where(Product.id.in_(requested_product_ids))).all()
        products_by_id = {p.id: p for p in products}

        missing = [pid for pid in requested_product_ids if pid not in products_by_id]
        if missing:
            raise HTTPException(status_code=404, detail=f"Products not found: {sorted(set(missing))}")

        items: list[PurchaseOrderItem] = []
        subtotal = Decimal("0")

        for item_in in payload.items:
            product = products_by_id[item_in.product_id]
            unit_price = Decimal(product.price)
            line_total = _money(unit_price * Decimal(item_in.quantity))
            subtotal += line_total

            items.append(
                PurchaseOrderItem(
                    product_id=product.id,
                    quantity=item_in.quantity,
                    unit_price=_money(unit_price),
                    line_total=line_total,
                )
            )

        subtotal = _money(subtotal)
        tax = _money(subtotal * TAX_RATE)
        total_amount = _money(subtotal + tax)

        reference_no = _generate_reference_no(db)
        po = PurchaseOrder(
            reference_no=reference_no,
            vendor_id=payload.vendor_id,
            subtotal=subtotal,
            tax=tax,
            total_amount=total_amount,
            status="DRAFT",
            items=items,
        )
        db.add(po)
        db.commit()

        po = db.scalar(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.vendor),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
            )
            .where(PurchaseOrder.id == po.id)
        )
        return po
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create purchase order") from e


@router.get("", response_model=list[PurchaseOrderOut])
def list_purchase_orders(db: Session = Depends(get_db)):
    try:
        return list(db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.id.desc())).all())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch purchase orders") from e


@router.get("/{po_id}", response_model=PurchaseOrderDetailOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    try:
        po = db.scalar(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.vendor),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
            )
            .where(PurchaseOrder.id == po_id)
        )
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        return po
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch purchase order") from e
