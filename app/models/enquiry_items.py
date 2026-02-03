from sqlalchemy import (
    Column, Integer, ForeignKey, DateTime,
    String, Numeric, Boolean
)
from sqlalchemy.sql import func
from app.db.session import Base


class EnquiryItem(Base):
    __tablename__ = "enquiry_items"

    id = Column(Integer, primary_key=True, index=True)

    enquiry_id = Column(
        Integer,
        ForeignKey("enquiries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id = Column(
        String(20),
        ForeignKey("products.product_id"),
        nullable=False
    )

    # Snapshot fields (DO NOT depend on Product later)
    product_name = Column(String(150), nullable=False)
    uom = Column(String(50))
    pack_size = Column(String(50))

    quantity = Column(Integer, nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
