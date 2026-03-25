import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from src.qa_agent.db.base import Base

class BugReportDB(Base):
    __tablename__ = "bug_reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("test_runs.id", ondelete="CASCADE"))
    title = Column(String)
    description = Column(Text)
