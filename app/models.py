from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class QuickBooksTokens(Base):
    __tablename__ = "quickbooks_tokens"

    id = Column(Integer, primary_key=True)
    realm_id = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
