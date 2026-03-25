import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from src.qa_agent.db.session import get_db
from src.qa_agent.db.tables.test_runs import TestRun
from src.qa_agent.tools.executor import stream_pytest_execution

router = APIRouter(prefix="/runs", tags=["Test Runs"])

class ExecuteRunInput(BaseModel):
    test_files: Optional[List[str]] = None
    markers: Optional[List[str]] = None
    target_base_url: str = "http://127.0.0.1:8001"

@router.post("/execute")
async def execute_tests(payload: ExecuteRunInput, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        result_batch = None
        async for event in stream_pytest_execution(
            test_files=payload.test_files,
            markers=payload.markers,
            target_base_url=payload.target_base_url,
        ):
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] == "result":
                result_batch = event
                try:
                    for tr in event.get("test_results", []):
                        db_row = TestRun(
                            run_batch_id     = tr["batch_id"],
                            req_id           = tr.get("req_id"),
                            tc_id            = tr.get("tc_id"),
                            test_name        = tr["test_name"],
                            filename         = tr["filename"],
                            status           = tr["status"],
                            duration_seconds = tr.get("duration"),
                            log_output       = None,
                            error_message    = tr.get("error_message"),
                        )
                        db.add(db_row)
                    await db.commit()
                    yield f"data: {json.dumps({'type': 'log', 'level': 'SUCCESS', 'message': '💾 Results saved to database'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'level': 'ERROR', 'message': f'❌ DB save failed: {str(e)}'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

@router.get("/")
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestRun).order_by(TestRun.created_at.desc()).limit(200)
    )
    return result.scalars().all()

@router.get("/{batch_id}")
async def get_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestRun).where(TestRun.run_batch_id == batch_id)
    )
    rows = result.scalars().all()
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Batch not found")
    return rows

@router.get("/{batch_id}/summary")
async def get_batch_summary(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestRun).where(TestRun.run_batch_id == batch_id)
    )
    rows = result.scalars().all()
    total   = len(rows)
    passed  = sum(1 for r in rows if r.status == "passed")
    failed  = sum(1 for r in rows if r.status == "failed")
    errors  = sum(1 for r in rows if r.status == "error")
    skipped = sum(1 for r in rows if r.status == "skipped")
    return {
        "batch_id":    batch_id,
        "total":       total,
        "passed":      passed,
        "failed":      failed,
        "errors":      errors,
        "skipped":     skipped,
        "pass_rate":   round((passed / total * 100), 1) if total > 0 else 0,
        "release_decision": "PASS" if failed == 0 and errors == 0 else "FAIL"
    }
