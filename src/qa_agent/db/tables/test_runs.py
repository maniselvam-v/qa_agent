import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from src.qa_agent.db.base import Base

class TestRun(Base):
    __tablename__ = "test_runs"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_batch_id     = Column(String, nullable=False, index=True)  # groups all tests in one execution
    req_id           = Column(String, nullable=True)               # REQ-101
    tc_id            = Column(String, nullable=True)               # TC-REQ-101-01
    test_name        = Column(String, nullable=False)              # test function name
    filename         = Column(String, nullable=False)              # test_REQ_101_guest_checkout.py
    status           = Column(String, nullable=False)              # pass | fail | error | skipped
    duration_seconds = Column(Float,  nullable=True)
    log_output       = Column(Text,   nullable=True)               # full stdout/stderr
    error_message    = Column(Text,   nullable=True)               # failure message if failed
    screenshot_path  = Column(String, nullable=True)               # for UI tests
    created_at       = Column(DateTime, default=datetime.utcnow)
