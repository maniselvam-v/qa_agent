import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from src.qa_agent.db.base import Base

class TestCaseDB(Base):
    __tablename__ = "test_cases"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("test_runs.id", ondelete="CASCADE"))
    req_id = Column(String)
    description = Column(Text)
