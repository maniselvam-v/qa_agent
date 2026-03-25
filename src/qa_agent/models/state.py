from typing import List, Dict
from pydantic import BaseModel, Field

from src.qa_agent.models.inputs import Requirement
from src.qa_agent.models.outputs import TestCase, BugReport

class PipelineState(BaseModel):
    """
    Global state moving through the single-run pipeline orchestrator.
    """
    # Phase 1: Inputs
    raw_brd_text: str = ""
    source_code_path: str = ""
    product_requirements: List[Requirement] = Field(default_factory=list)
    
    # Phase 2: Planning & Code Gen
    test_cases: List[TestCase] = Field(default_factory=list)
    generated_test_scripts: Dict[str, str] = Field(default_factory=dict) # filename -> content
    
    # Phase 3: Execution
    test_results: Dict[str, str] = Field(default_factory=dict) # filename -> pass/fail
    test_logs: str = ""
    
    # Phase 4: Outputs
    bug_reports: List[BugReport] = Field(default_factory=list)
    ci_cd_signal: str = "pending"
