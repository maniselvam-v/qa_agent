from fastapi import APIRouter
from pydantic import BaseModel
from src.qa_agent.agents.planner import planner_agent

router = APIRouter(prefix="/requirements", tags=["Requirements"])

class QAInputRequest(BaseModel):
    brd_text: str
    frd_text: str
    github_repo_url: str

@router.post("/analyze")
async def generate_structured_inputs(req: QAInputRequest):
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info("====================================")
    logger.info(f"🚀 Received QA Analyze Request!")
    logger.info(f"Target Repo: {req.github_repo_url}")
    logger.info("Running Pydantic AI Planner Agent (Bedrock)... This may take a few minutes!")
    
    prompt = f"Analyze the following BRD and FRD functionality for the repository: {req.github_repo_url}\\n\\nBRD:\\n{req.brd_text}\\n\\nFRD:\\n{req.frd_text}"
    
    # Execute the Pydantic AI planner agent against Bedrock
    planner_res = await planner_agent.run(prompt)
    
    logger.info("Running Pydantic AI Feature Classifier Agent...")
    from src.qa_agent.agents.classifier_agent import classifier_agent
    requirements_text = "\\n\\n".join([
        f"req_id: {r.id}\\ndescription: {r.description}"
        for r in planner_res.output.requirements
    ])
    classification_result = await classifier_agent.run(
        f"Classify these requirements:\\n\\n{requirements_text}"
    )
    
    classifications = [c.model_dump() for c in classification_result.output.classifications]
    classification_map = {c["req_id"]: c["feature_types"] for c in classifications}
    
    requirements_with_types = []
    for req in planner_res.output.requirements:
        req_dict = req.model_dump()
        req_dict["feature_types"] = classification_map.get(req_dict["id"], ["api"])
        requirements_with_types.append(req_dict)
    
    logger.info(f"✅ Planner & Classifier Agents Completed! Generated {len(requirements_with_types)} Reqs & {len(planner_res.output.test_cases)} Test Cases.")
    logger.info("====================================")
    
    return {
        "status": "success",
        "requirements": requirements_with_types,
        "classifications": classifications,
        "test_cases": planner_res.output.test_cases
    }

