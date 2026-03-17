from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import MoneyModel, ORMBaseModel
from app.schemas.product import ProductOut
from app.schemas.vendor import VendorOut


class PurchaseOrderItemCreate(ORMBaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class PurchaseOrderCreate(ORMBaseModel):
    vendor_id: int
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderItemOut(MoneyModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product: ProductOut


class PurchaseOrderOut(MoneyModel):
    id: int
    reference_no: str
    vendor_id: int
    created_at: datetime
    subtotal: Decimal
    tax: Decimal
    total_amount: Decimal
    status: str


class PurchaseOrderDetailOut(PurchaseOrderOut):
    vendor: VendorOut
    items: list[PurchaseOrderItemOut]

