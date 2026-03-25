from typing import Dict, List
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from src.qa_agent.models.outputs import TestCase
from src.qa_agent.config import settings

class CoderResult(BaseModel):
    scripts: dict[str, str] = Field(
        description="Dictionary mapping filename (e.g., test_login.py) to script string"
    )

# Define the Coder Agent
coder_agent = Agent(
    settings.llm_model,
    output_type=CoderResult,
    system_prompt=(
        "You are an expert SDET (Software Development Engineer in Test). "
        "Your task is to take a list of Test Cases and write highly robust, modular Pytest scripts for them. "
        "Ensure all test functions have clear docstrings, arrange/act/assert patterns, and proper mocking where appropriate. "
        "Return the filename and its exact python code."
    )
)
