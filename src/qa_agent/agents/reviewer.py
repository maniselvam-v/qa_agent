from typing import List
from pydantic_ai import Agent
from src.qa_agent.models.outputs import BugReport, QAExecutionMetrics
from pydantic import BaseModel, Field
from src.qa_agent.config import settings

class ReviewerResult(BaseModel):
    bug_reports: list[BugReport] = Field(description="List of defects found in execution")
    metrics: QAExecutionMetrics = Field(description="Execution summary metrics")

# Define the Reviewer Agent
reviewer_agent = Agent(
    settings.llm_model,
    output_type=ReviewerResult,
    system_prompt=(
        "You are an expert QA Manager and Bug Triager. "
        "Your task is to review execution logs and test results. "
        "If any tests failed, analyze the logs to generate highly detailed Bug Reports containing steps to reproduce. "
        "Then, summarize the execution metrics."
    )
)
