from fastapi import APIRouter, Query
from typing import Optional

from services import normalizer
from schemas.unified import UnifiedCostEntry, CostSummary

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("", response_model=list[UnifiedCostEntry])
def list_costs(
    provider: Optional[str] = Query(None, description="Filter by provider: aws | gcp | azure"),
):
    return normalizer.get_all_costs(provider=provider)


@router.get("/summary", response_model=CostSummary)
def cost_summary():
    return normalizer.get_cost_summary()
