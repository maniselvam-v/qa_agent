from fastapi import APIRouter

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

@router.post("/github")
def github_webhook():
    return {"message": "Handles new PRs to trigger Git Analyzer tool"}

@router.post("/ci")
def ci_webhook():
    return {"message": "Handles CI pipeline build signals"}
