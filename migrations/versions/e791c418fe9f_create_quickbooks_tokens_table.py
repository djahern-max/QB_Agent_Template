from app.database import engine
from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class QuickBooksTokens(Base):
    __tablename__ = "quickbooks_tokens"

    id = Column(Integer, primary_key=True)
    realm_id = Column(String, nullable=False)
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
    summary = Column(Text)
    positive_insights = Column(Text)
    concerns = Column(Text)
    recommendations = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


def create_tables():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


if __name__ == "__main__":
    create_tables()
