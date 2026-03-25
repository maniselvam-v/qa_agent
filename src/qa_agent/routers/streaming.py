from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.qa_agent.routers.requirements import QAInputRequest
from src.qa_agent.agents.planner import planner_agent
from src.qa_agent.agents.classifier_agent import classifier_agent
from src.qa_agent.agents.coder import coder_agent
import json
import asyncio
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

def log_event(message: str, level: str = "INFO") -> str:
    """Format a single SSE log line."""
    logger.info(message)
    payload = json.dumps({"level": level, "message": message})
    return f"data: {payload}\n\n"

@router.post("/requirements/analyze/stream")
async def analyze_stream(payload: QAInputRequest):
    """
    Streaming version of /requirements/analyze.
    Pushes log lines via SSE as each step completes.
    Final line pushes the full result as a special RESULT event.
    """

    async def event_generator():
        try:
            yield log_event("🚀 Pipeline started", "INFO")
            await asyncio.sleep(0.1)

            # ── STEP 1: Validate inputs ──────────────────────────
            yield log_event("📄 Validating BRD and FRD inputs...", "INFO")
            await asyncio.sleep(0.2)

            brd_text = payload.brd_text or ""
            frd_text = payload.frd_text or ""

            brd_len = len(brd_text.strip().split())
            frd_len = len(frd_text.strip().split()) if frd_text else 0

            yield log_event(f"✅ BRD loaded — {brd_len} words", "SUCCESS")
            if frd_len:
                yield log_event(f"✅ FRD loaded — {frd_len} words", "SUCCESS")
            else:
                yield log_event("⚠️  No FRD provided — continuing with BRD only", "WARN")
            await asyncio.sleep(0.1)

            # ── STEP 2: Planner Agent ────────────────────────────
            yield log_event("🤖 Planner Agent starting — extracting requirements...", "INFO")
            yield log_event("⏳ Calling LLM (this may take 30–60 seconds)...", "INFO")

            prompt = f"Analyze the following BRD and FRD functionality for the repository: {payload.github_repo_url or ''}\\n\\nBRD:\\n{brd_text}\\n\\nFRD:\\n{frd_text}"

            planner_result = await planner_agent.run(
                prompt,
                model_settings={"max_tokens": 8192}
            )
            req_list_models = planner_result.output.requirements
            req_list = [r.model_dump() for r in req_list_models]

            yield log_event(f"✅ Planner Agent done — {len(req_list)} requirements extracted", "SUCCESS")
            for r in req_list[:5]:
                yield log_event(f"   → {r.get('id', '?')} : {r.get('description', '')[:70]}...", "DETAIL")
            if len(req_list) > 5:
                yield log_event(f"   → ... and {len(req_list)-5} more", "DETAIL")
            await asyncio.sleep(0.1)

            # ── STEP 3: Classifier Agent ─────────────────────────
            yield log_event("🏷️  Feature Classifier starting — tagging test types...", "INFO")
            yield log_event("⏳ Calling LLM for classification...", "INFO")

            requirements_text = "\\n\\n".join([
                f"req_id: {r.get('id')}\\ndescription: {r.get('description')}"
                for r in req_list
            ])
            classification_result = await classifier_agent.run(
                f"Classify these requirements:\\n\\n{requirements_text}"
            )
            
            classifications = [c.model_dump() for c in classification_result.output.classifications]

            yield log_event(f"✅ Classifier done — {len(classifications)} requirements tagged", "SUCCESS")
            for c in classifications[:5]:
                types_str = ", ".join(c.get("feature_types", []))
                yield log_event(f"   → {c.get('req_id')} : [{types_str}]", "DETAIL")
            if len(classifications) > 5:
                yield log_event(f"   → ... and {len(classifications)-5} more", "DETAIL")
            await asyncio.sleep(0.1)

            # Merge feature types into requirements
            classification_map = {c["req_id"]: c["feature_types"] for c in classifications}
            for req in req_list:
                req["feature_types"] = classification_map.get(req.get("id"), ["api"])

            # ── STEP 4: Test Case Generation ─────────────────────
            yield log_event("🧪 Test Case Generator starting...", "INFO")
            yield log_event("⏳ Retrieving generated test cases...", "INFO")

            # Extract test cases from planner since they generate in the same prompt pass currently
            test_cases_models = planner_result.output.test_cases
            test_cases = [tc.model_dump() for tc in test_cases_models]

            yield log_event(f"✅ Test Case Generator done — {len(test_cases)} test cases generated", "SUCCESS")

            positive = [t for t in test_cases if t.get("type") == "positive"]
            negative = [t for t in test_cases if t.get("type") == "negative"]
            edge     = [t for t in test_cases if t.get("type", "").lower() == "edge"]
            yield log_event(f"   → 🟢 {len(positive)} positive  🔴 {len(negative)} negative  🟠 {len(edge)} edge", "DETAIL")
            await asyncio.sleep(0.1)

            # ── STEP 5: Build final response ─────────────────────
            yield log_event("📦 Building final response...", "INFO")

            final_result = {
                "status": "success",
                "requirements": req_list,
                "classifications": classifications,
                "test_cases": test_cases,
            }

            yield log_event(f"✅ Pipeline complete — {len(req_list)} requirements · {len(test_cases)} test cases", "SUCCESS")
            yield log_event("─" * 60, "DIVIDER")

            result_payload = json.dumps({"type": "RESULT", "data": final_result})
            yield f"data: {result_payload}\n\n"

        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            logger.error(f"PIPELINE EXCEPTION:\n{full_trace}")
            
            # Send simplified error to UI
            yield log_event(f"❌ Pipeline failed: {str(e)}", "ERROR")
            error_payload = json.dumps({"type": "ERROR", "message": f"{type(e).__name__}: {str(e)}"})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
