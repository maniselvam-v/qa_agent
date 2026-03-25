import uuid
from sqlalchemy import Column, String
from src.qa_agent.db.base import Base

class PRReviewDB(Base):
    __tablename__ = "pr_reviews"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
