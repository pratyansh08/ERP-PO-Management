from decimal import Decimal

from pydantic import EmailStr, Field

from app.schemas.base import ORMBaseModel


class VendorCreate(ORMBaseModel):
    name: str
    contact: str | None = None
    rating: Decimal = Field(default=Decimal("0.0"), ge=0, le=5)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class VendorUpdate(ORMBaseModel):
    name: str | None = None
    contact: str | None = None
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class VendorOut(ORMBaseModel):
    id: int
    name: str
    contact: str | None = None
    rating: Decimal
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

