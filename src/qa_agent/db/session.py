from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine # Added this import
from src.qa_agent.config import settings

engine = create_async_engine( # Changed create_engine to create_async_engine
    settings.resolved_database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.resolved_database_url else {} # Changed database_url to resolved_database_url in two places
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
