from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)

    # Business ID (safe to expose)
    admin_id = Column(String(20), unique=True, nullable=True, index=True)

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)

    #  Hashed password only
    password_hash = Column(String(255), nullable=False)

    # Role & permissions
    role = Column(String(50), default="admin")  
    is_super_admin = Column(Boolean, default=False)
    # role = Column(String(50), default="admin")

    # Status flags
    is_active = Column(Boolean, default=True)

    # Tracking
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("username"),
        UniqueConstraint("email"),
    )

