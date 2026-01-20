from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    product_id = Column(String(20), unique=True, nullable=False)
    category_id = Column(String(20), ForeignKey("categories.category_id"))
    name = Column(String(150))
    description = Column(Text)
    price = Column(Numeric(10,2))
    min_order_qty = Column(Integer)
    stock = Column(Integer)
    image = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
