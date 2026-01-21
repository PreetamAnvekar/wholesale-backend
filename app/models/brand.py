from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    image = Column(String(255))
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime,server_default=func.now(), onupdate=func.now())
    