from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from app.db.session import Base


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)

    # Session-based cart (guest users)
    session_id = Column(String(200), nullable=False, index=True)

    # Future logged-in users
    user_id = Column(Integer, nullable=True, index=True)

    product_id = Column(
        String(20),
        ForeignKey("products.product_id", ondelete="CASCADE"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)

    # Optional tracking (recommended)
    ip_address = Column(String(50))
    user_agent = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("session_id", "product_id", name="uq_cart_session_product"),
    )
