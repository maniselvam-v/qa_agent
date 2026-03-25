from typing import List, Optional
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    id: str = Field(description="Unique ID for the test case (e.g., TC-REQ-101-01).")
    req_id: str = Field(description="ID of the requirement this test case verifies.")
    description: str = Field(description="What the test case verifies.")
    type: str = Field(description="Type of test: positive, negative, edge, etc.")
    steps: List[str] = Field(description="Step by step instructions to execute the test.")
    expected_result: str = Field(description="The expected outcome if the test passes.")

class BugReport(BaseModel):
    title: str = Field(description="A concise title summarizing the bug.")
    description: str = Field(description="Detailed description of the observed behavior versus expected behavior.")
    steps_to_reproduce: List[str] = Field(description="Step by step instructions to reproduce the bug.")
    logs: Optional[str] = Field(None, description="Relevant execution logs capturing the failure.")
    severity: str = Field(description="Priority/Severity level (e.g., High, Medium, Low).")

class QAExecutionMetrics(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate_percentage: float
    new_bugs_logged: int

class FeatureClassification(BaseModel):
    req_id: str
    description: str
    feature_types: List[str]
    reasoning: str
