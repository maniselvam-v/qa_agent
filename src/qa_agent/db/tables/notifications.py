import uuid
from sqlalchemy import Column, String
from src.qa_agent.db.base import Base

class NotificationDB(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
