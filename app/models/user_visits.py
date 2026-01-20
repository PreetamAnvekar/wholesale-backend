from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class UserVisit(Base):
    __tablename__ = "user_visits"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(200))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    visited_page = Column(String(200))
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
