from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, Numeric, UniqueConstraint
)
from sqlalchemy.sql import func
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    product_id = Column(String(20), unique=True, nullable=True, index=True)

    category_id = Column(
        String(20),
        ForeignKey("categories.category_id"),
        nullable=False,
        index=True
    )

    brand_id = Column(
        String(20),
        ForeignKey("brands.brand_id"),
        nullable=False,
        index=True
    )

    name = Column(String(150), nullable=False, index=True)

    description = Column(Text)

    sku = Column(String(50), unique=True)

    mrp = Column(Numeric(10, 2), nullable=False)

    price = Column(Numeric(10, 2), nullable=False, index=True)

    pack_size = Column(Integer, nullable=False)  # e.g. 50 pens

    uom = Column(String(20), nullable=False)  # PCS / BOX / REAM

    min_order_qty = Column(Integer, nullable=False, default=1)

    stock = Column(Integer, nullable=False, default=0)

    image = Column(String(255))

    hsn_code = Column(String(20))

    tax_percent = Column(Numeric(5, 2), default=0)

    is_featured = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

   

    __table_args__ = (
        UniqueConstraint("name"),
        UniqueConstraint("sku"),
    )
