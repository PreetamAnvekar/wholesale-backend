from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from app.db.session import Base

class EnquiryItem(Base):
    __tablename__ = "enquiry_items"

    id = Column(Integer, primary_key=True)
    enquiry_id = Column(Integer, ForeignKey("enquiries.id"))
    product_id = Column(String(20), ForeignKey("products.product_id"))
    quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
