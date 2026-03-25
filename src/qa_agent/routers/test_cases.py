from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.qa_agent.db.session import SessionLocal # Assuming get_db is standard or we remove it if unused
from src.qa_agent.agents.coder_agent import coder_agent, CoderResult
from src.qa_agent.tools.script_writer import write_test_file, write_manifest
from src.qa_agent.models.outputs import TestCase
from src.qa_agent.models.inputs import Requirement
from pydantic import BaseModel
from typing import List
import asyncio

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])

@router.get("/")
def list_test_cases():
    return {"message": "List of test cases"}

@router.post("/generate")
def generate_test_cases():
    return {"message": "Generates test cases via Planner Agent"}

class GenerateScriptsInput(BaseModel):
    requirements: List[dict]     # from session state / previous analyze response
    test_cases: List[dict]       # from session state / previous analyze response
    classifications: List[dict]  # from session state / previous analyze response
    target_base_url: str = "http://127.0.0.1:8001"


class GenerateScriptsResponse(BaseModel):
    status: str
    total_files: int
    files: List[dict]
    manifest_path: str


@router.post("/generate-scripts", response_model=GenerateScriptsResponse)
async def generate_scripts(payload: GenerateScriptsInput):
    """
    Takes requirements + test cases from the analyze step and
    generates executable pytest files for each requirement.
    Runs coder agent calls in parallel — one per requirement.
    """

    # Build classification lookup
    type_map = {
        c["req_id"]: c.get("feature_types", ["api"])
        for c in payload.classifications
    }

    # Group test cases by requirement
    tc_by_req = {}
    for tc in payload.test_cases:
        req_id = tc.get("req_id")
        if req_id not in tc_by_req:
            tc_by_req[req_id] = []
        tc_by_req[req_id].append(tc)

    async def generate_for_requirement(req: dict) -> dict:
        req_id = req["id"]
        tcs = tc_by_req.get(req_id, [])
        feature_types = type_map.get(req_id, ["api"])

        prompt = f"""
Generate a complete pytest file for this requirement.

Requirement ID: {req_id}
Description: {req["description"]}
Feature Types: {", ".join(feature_types)}
Target Base URL: {payload.target_base_url}

Acceptance Criteria:
{chr(10).join(f"- {ac}" for ac in req.get("acceptance_criteria", []))}

Test Cases to implement ({len(tcs)} total):
{chr(10).join([
    f"  {tc['id']} [{tc['type']}]: {tc['description']}"
    + f"{chr(10)}    Steps: {'; '.join(tc.get('steps', []))}"
    + f"{chr(10)}    Expected: {tc.get('expected_result', '')}"
    for tc in tcs
])}
"""
        result = await coder_agent.run(
            prompt, 
            model_settings={"max_tokens": 8192}
        )
        print(f"🤖 LLM RAW OUTPUT FOR {req_id}: {result.output}")
        return result.output.test_files[0] if result.output.test_files else None

    # Run requirements sequentially to avoid AWS Bedrock rate-limiting
    import traceback
    written_files = []
    
    print("-" * 50)
    print(f"🚀 Starting code generation for {len(payload.requirements)} requirements sequentially...")
    print("-" * 50)

    for idx, req in enumerate(payload.requirements, 1):
        req_id = req["id"]
        print(f"[{idx}/{len(payload.requirements)}] ⚙️ Processing {req_id}...")
        try:
            item = await generate_for_requirement(req)
            if item:
                filepath = write_test_file(item.filename, item.code)
                written_files.append({
                    "req_id": item.req_id,
                    "filename": item.filename,
                    "filepath": filepath,
                    "frameworks_used": item.frameworks_used
                })
                print(f"    ✅ Successfully generated {item.filename}")
            else:
                print(f"    ⚠️ Warning: LLM returned None for {req_id}")
        except Exception as e:
            print(f"    ❌ ERROR on {req_id}: {e}")
            traceback.print_exception(type(e), e, e.__traceback__)

    print("-" * 50)
    print(f"🎉 Completed code generation. Wrote {len(written_files)} files.")
    print("-" * 50)

    manifest_path = write_manifest(written_files)

    return GenerateScriptsResponse(
        status="success",
        total_files=len(written_files),
        files=written_files,
        manifest_path=manifest_path
    )
