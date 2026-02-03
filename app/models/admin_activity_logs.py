from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(String, ForeignKey("admin_users.admin_id", ondelete="CASCADE"))
    action = Column(String(100))
    module = Column(String(100))
    endpoint = Column(String(100))
    method = Column(String(10))
    description = Column(Text)
    ip_address = Column(String(50))
    payload = Column(Text) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
