from decimal import Decimal

from pydantic import Field

from app.schemas.base import MoneyModel, ORMBaseModel


class ProductCreate(ORMBaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(gt=0)
    stock_level: int = Field(default=0, ge=0)


class ProductUpdate(ORMBaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    price: Decimal | None = Field(default=None, gt=0)
    stock_level: int | None = Field(default=None, ge=0)


class ProductOut(MoneyModel):
    id: int
    sku: str
    name: str
    price: Decimal
    stock_level: int

