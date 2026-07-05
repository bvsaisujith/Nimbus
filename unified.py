"""
Unified schema definitions.

Every cloud adapter (aws_adapter.py, gcp_adapter.py, azure_adapter.py) must
return data conforming to these models. This is the contract the rest of
the system (normalizer, routers, frontend) depends on. See SRS.md section 6.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


ProviderName = Literal["aws", "gcp", "azure"]
ResourceType = Literal["compute", "storage", "database", "network", "other"]
DataSource = Literal["live", "mock", "error"]


class UnifiedResource(BaseModel):
    id: str
    provider: ProviderName
    type: ResourceType
    name: str
    region: str
    status: str
    tags: dict[str, str] = Field(default_factory=dict)
    source: DataSource
    raw: dict = Field(default_factory=dict)


class UnifiedCostEntry(BaseModel):
    provider: ProviderName
    service: str
    granularity: Literal["DAILY", "MONTHLY"] = "MONTHLY"
    period_start: str
    period_end: str
    amount_usd: float
    type: Literal["actual", "estimated"] = "actual"
    source: DataSource


class ProviderStatus(BaseModel):
    provider: ProviderName
    resources_source: DataSource
    cost_source: DataSource
    error_message: Optional[str] = None


class CostSummary(BaseModel):
    total_usd: float
    by_provider: dict[str, float]
    as_of: str
