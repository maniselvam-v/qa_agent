from fastapi import APIRouter

router = APIRouter(tags=["Metrics"])

@router.get("/metrics")
def get_metrics():
    return {"message": "Retrieves QA execution metrics"}

@router.get("/dashboard")
def get_dashboard_summary():
    return {"message": "Retrieves summary for QA dashboard"}
