from pydantic_ai import Agent
from src.qa_agent.config import settings

reporter_agent = Agent(
    settings.llm_model,
    system_prompt="You are a QA Reporter. Summarize test results."
)
