from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class UserVisit(Base):
    __tablename__ = "user_visits"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String(200), index=True)   # frontend generated UUID
    ip_address = Column(String(50))                # client IP
    user_agent = Column(Text)                      # browser/device info
    visited_page = Column(String(255))             # URL or route
    referer = Column(String(255), nullable=True)                 # from where user came

    device_type = Column(String(50))               # mobile / desktop
    browser = Column(String(50))                   # chrome / firefox
    os = Column(String(50))                        # windows / android

    visited_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False
)
