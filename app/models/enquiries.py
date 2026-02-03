from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean
)
from sqlalchemy.sql import func
from app.db.session import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)

    # Customer info
    customer_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)

    # Session tracking
    session_id = Column(String(200), nullable=False, index=True)

    # Status workflow
    status = Column(
        String(30),
        default="NEW",   # NEW, CONTACTED, QUOTED, CLOSED, CANCELLED
        nullable=False,
        index=True
    )

    # Admin actions
    assigned_admin_id = Column(Integer, nullable=True)
    admin_notes = Column(Text, nullable=True)

    # Tracking
    ip_address = Column(String(50))
    user_agent = Column(String(255))

    # Soft delete (important)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
