from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class QuickBooksTokens(Base):
    __tablename__ = "quickbooks_tokens"

    id = Column(Integer, primary_key=True)
    realm_id = Column(String, nullable=False)  # Changed from realm to realm_id
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class FinancialAnalysis(Base):
    __tablename__ = "financial_analyses"

    id = Column(Integer, primary_key=True)
    realm_id = Column(
        String, nullable=False
    )  # Foreign key relation to QuickBooksTokens
    analysis_date = Column(DateTime, server_default=func.now())
    summary = Column(Text)
    positive_insights = Column(Text)  # Store as JSON string
    concerns = Column(Text)  # Store as JSON string
    recommendations = Column(Text)  # Store as JSON string
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
