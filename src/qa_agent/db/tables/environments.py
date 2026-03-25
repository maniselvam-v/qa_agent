import uuid
from sqlalchemy import Column, String
from src.qa_agent.db.base import Base

class EnvironmentDB(Base):
    __tablename__ = "environments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
