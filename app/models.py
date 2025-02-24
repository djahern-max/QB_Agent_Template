from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class QuickBooksTokens(Base):
    __tablename__ = "quickbooks_tokens"

    id = Column(Integer, primary_key=True)
    realm = Column(String, nullable=False)  # QuickBooks company ID
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
