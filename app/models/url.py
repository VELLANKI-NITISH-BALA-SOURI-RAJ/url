from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(Text, nullable=False)
    short_code = Column(String(12), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    password_hash = Column(String(128), nullable=True)
    is_active = Column(Integer, server_default="1") # 1 for active, 0 for inactive
    
    analytics = relationship("Analytics", back_populates="url", cascade="all, delete-orphan")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(50))
    user_agent = Column(Text)
    referer = Column(Text)

    url = relationship("URL", back_populates="analytics")

# Index for performance on code lookups is already handled by index=True in the Column definition

