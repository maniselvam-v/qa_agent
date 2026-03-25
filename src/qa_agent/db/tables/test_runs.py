import uuid
from sqlalchemy import Column, String, DateTime, func
from src.qa_agent.db.base import Base

class TestRun(Base):
    __tablename__ = "test_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")
    pr_url = Column(String)
    created_at = Column(DateTime, default=func.now())
