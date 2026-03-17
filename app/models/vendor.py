from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (CheckConstraint("rating >= 0 AND rating <= 5", name="ck_vendors_rating_0_5"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=Decimal("0.0"))
    email: Mapped[str | None] = mapped_column(String(254), nullable=True, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    purchase_orders = relationship("PurchaseOrder", back_populates="vendor", cascade="all, delete-orphan")

