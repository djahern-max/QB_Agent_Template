import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import Base, QuickBooksTokens, FinancialAnalysis


def create_all_tables():
    # Create all tables defined in your models
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

    # Verify tables exist
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in database:", tables)


if __name__ == "__main__":
    create_all_tables()
