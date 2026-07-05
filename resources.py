from fastapi import APIRouter, Query
from typing import Optional

from services import normalizer
from schemas.unified import UnifiedResource

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("", response_model=list[UnifiedResource])
def list_resources(
    provider: Optional[str] = Query(None, description="Filter by provider: aws | gcp | azure"),
    type: Optional[str] = Query(None, description="Filter by type: compute | storage | database | network"),
):
    return normalizer.get_all_resources(provider=provider, type=type)
