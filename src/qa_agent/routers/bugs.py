from fastapi import APIRouter

router = APIRouter(prefix="/bugs", tags=["Bugs"])

@router.get("/")
def list_bugs():
    return {"message": "List of bug reports"}

@router.post("/{bug_id}/sync-jira")
def sync_bug_to_jira(bug_id: str):
    return {"message": "Syncs the given bug report to Jira via tool"}
