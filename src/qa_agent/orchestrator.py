from typing import Optional
from pydantic_ai.models.test import TestModel

from src.qa_agent.models.state import PipelineState
from src.qa_agent.agents.planner import planner_agent
from src.qa_agent.agents.classifier_agent import classifier_agent
from src.qa_agent.agents.coder import coder_agent
from src.qa_agent.agents.reviewer import reviewer_agent
from src.qa_agent.tools.environment import setup_test_environment
from src.qa_agent.tools.executor import execute_test_scripts
from src.qa_agent.tools.integration import send_slack_notification, log_metrics_to_cloudwatch, signal_ci_cd

class QAOrchestrator:
    def __init__(self, use_test_model: bool = True):
        # Use Pydantic AI's TestModel by default so it runs without an OpenAI API key
        self.model = TestModel() if use_test_model else None
        
    def run_pipeline(self, raw_brd: str) -> PipelineState:
        print("\\n=== STARTING QA PIPELINE ===")
        state = PipelineState(raw_brd_text=raw_brd)
        
        # 1 & 2 & 3. Planning Phase
        print("\\n[1] PLANNER AGENT RUNNING...")
        planner_res = planner_agent.run_sync(
            f"Extract requirements and test cases from: {state.raw_brd_text}",
            model=self.model
        )
        state.product_requirements = planner_res.output.requirements
        state.test_cases = planner_res.output.test_cases
        print(f"    Extracted {len(state.product_requirements)} reqs and {len(state.test_cases)} test cases.")
        
        print("\\n[1.5] CLASSIFIER AGENT RUNNING...")
        requirements_text = "\\n\\n".join([f"req_id: {r.id}\\ndescription: {r.description}" for r in state.product_requirements])
        classification_result = classifier_agent.run_sync(
            f"Classify these requirements:\\n\\n{requirements_text}",
            model=self.model
        )
        
        state.feature_classifications = [c.model_dump() for c in classification_result.output.classifications]
        classification_map = {c["req_id"]: c["feature_types"] for c in state.feature_classifications}
        
        for req in state.product_requirements:
            if not hasattr(req, "feature_types"):
                req.feature_types = classification_map.get(req.id, ["api"])
        
        # 4. Coding Phase
        print("\\n[2] CODER AGENT RUNNING...")
        tc_json = [tc.model_dump_json() for tc in state.test_cases]
        coder_res = coder_agent.run_sync(
            f"Generate Pytest scripts for these test cases: {tc_json}",
            model=self.model
        )
        state.generated_test_scripts = coder_res.output.scripts
        print(f"    Generated {len(state.generated_test_scripts)} automation scripts.")
        
        # 5. Environment Setup
        print("\\n[3] ENVIRONMENT TOOL RUNNING...")
        setup_test_environment()
        
        # 6. Test Execution
        print("\\n[4] EXECUTOR TOOL RUNNING...")
        results, logs = execute_test_scripts(state.generated_test_scripts)
        state.test_results = results
        state.test_logs = logs
        
        # 7 & 8. Reviewing Phase
        print("\\n[5] REVIEWER AGENT RUNNING...")
        reviewer_res = reviewer_agent.run_sync(
            f"Analyze test logs: {state.test_logs}. Results: {state.test_results}",
            model=self.model
        )
        state.bug_reports = reviewer_res.output.bug_reports
        
        # 9, 10, 11, 12. Integration & Feedback
        print("\\n[6] INTEGRATION TOOLS RUNNING...")
        log_metrics_to_cloudwatch(reviewer_res.output.metrics.model_dump())
        
        passed = len(state.bug_reports) == 0
        state.ci_cd_signal = "PASS" if passed else "FAIL"
        
        signal_ci_cd(passed)
        send_slack_notification(f"Pipeline finished with status {state.ci_cd_signal}")
        
        print("\\n=== PIPELINE FINISHED ===")
        return state
