from fastapi import FastAPI
from src.qa_agent.config import settings
from src.qa_agent.routers import requirements, test_cases, test_runs, bugs, metrics, webhooks, streaming

app = FastAPI(title=settings.app_name, version="0.3.0")

# Include all modular routers
app.include_router(requirements.router)
app.include_router(test_cases.router)
app.include_router(test_runs.router)
app.include_router(bugs.router)
app.include_router(metrics.router)
app.include_router(webhooks.router)
app.include_router(streaming.router, tags=["Streaming"])

@app.get("/")
def root():
    return {"message": f"Welcome to the {settings.app_name}!"}
