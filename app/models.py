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
    realm_id = Column(String, nullable=False)
    analysis_date = Column(DateTime, server_default=func.now())

    # Keep existing fields
    summary = Column(Text)
    positive_insights = Column(Text)
    concerns = Column(Text)
    recommendations = Column(Text)

    # Add fields to store raw statement data (optional)
    profit_loss_data = Column(Text)  # Store as JSON string
    balance_sheet_data = Column(Text)  # Store as JSON string
    cash_flow_data = Column(Text)  # Store as JSON string

    # Add fields to store trend data
    trend_data = Column(Text)  # Store trends as JSON string

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
