import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from src.qa_agent.db.base import Base

class RequirementDB(Base):
    __tablename__ = "requirements"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("test_runs.id", ondelete="CASCADE"))
    req_id = Column(String, index=True)
    description = Column(Text)
