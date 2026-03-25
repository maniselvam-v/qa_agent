from typing import List
from pydantic import BaseModel, Field

class Requirement(BaseModel):
    id: str = Field(description="Unique ID for the requirement (e.g., REQ-101).")
    description: str = Field(description="Detailed description of the requirement.")
    acceptance_criteria: List[str] = Field(description="List of criteria that must be met to consider the requirement fulfilled.")
