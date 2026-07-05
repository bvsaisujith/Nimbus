from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import resources, costs
from services import normalizer
from schemas.unified import ProviderStatus

app = FastAPI(title="Multi-Cloud Unified Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resources.router)
app.include_router(costs.router)


@app.get("/api/health", response_model=list[ProviderStatus])
def health():
    """Per-provider adapter status: live, mock, or error. Check this first
    when something looks wrong on the dashboard."""
    return normalizer.get_provider_statuses()


@app.get("/")
def root():
    return {"status": "ok", "service": "multi-cloud-dashboard-api"}
