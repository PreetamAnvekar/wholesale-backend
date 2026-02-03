from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)   # internal PK

    category_id = Column(String(20), unique=True, nullable=True)  # example: CAT001, CAT002
    parent_id = Column(String(20), ForeignKey("categories.category_id"), nullable=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String)
    image = Column(String, nullable=False)

    is_active = Column(Boolean, default=True, index=True)
    parent = relationship(
        "Category",
        remote_side=[category_id],
        backref="subcategories"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("name"),
    )

    products = relationship("Product", backref="category")
