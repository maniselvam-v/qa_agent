import uuid
from sqlalchemy import Column, String
from src.qa_agent.db.base import Base

class AuditLogDB(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
