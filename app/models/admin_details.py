from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.db.session import Base

class AdminDetail(Base):
    __tablename__ = "admin_details"

    id = Column(Integer, primary_key=True)

    admin_id = Column(
        String(20),
        ForeignKey("admin_users.admin_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Examples: phone, address, profile_image, permissions
    detail_type = Column(String(50), nullable=False)
    detail_value = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("admin_id", "detail_type", name="uq_admin_detail"),
        Index("idx_admin_detail_type", "detail_type"),
    )
