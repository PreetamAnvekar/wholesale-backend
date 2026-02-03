from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Brand(Base):
    __tablename__ = "brands"

    # Internal primary key
    id = Column(Integer, primary_key=True, index=True)

    # Business ID (BRD0001)
    brand_id = Column(String(20), unique=True, nullable=True, index=True)

    name = Column(String(100), nullable=False)
    image = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    products = relationship("Product", backref="brand")

    __table_args__ = (
        UniqueConstraint("name"),
    )
