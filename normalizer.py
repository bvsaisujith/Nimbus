"""
Normalizer service.

This is the ONLY place that combines data across clouds. Routers should
call these functions rather than calling adapters directly, so that adding
AWS/Azure later means changing this file, not the routers.
"""

from datetime import datetime, timezone

from adapters import gcp_adapter
from schemas.unified import UnifiedResource, UnifiedCostEntry, ProviderStatus, CostSummary

# NOTE: aws_adapter / azure_adapter will be imported here once built.
# from adapters import aws_adapter, azure_adapter


def get_all_resources(provider: str | None = None, type: str | None = None) -> list[UnifiedResource]:
    all_resources: list[UnifiedResource] = []

    gcp_resources, _ = gcp_adapter.get_gcp_resources()
    all_resources += gcp_resources

    # aws_resources, _ = aws_adapter.get_aws_resources()
    # all_resources += aws_resources
    # azure_resources, _ = azure_adapter.get_azure_resources()
    # all_resources += azure_resources

    if provider:
        all_resources = [r for r in all_resources if r.provider == provider]
    if type:
        all_resources = [r for r in all_resources if r.type == type]

    return all_resources


def get_all_costs(provider: str | None = None) -> list[UnifiedCostEntry]:
    all_costs: list[UnifiedCostEntry] = []

    gcp_costs, _ = gcp_adapter.get_gcp_costs()
    all_costs += gcp_costs

    # aws_costs, _ = aws_adapter.get_aws_costs()
    # all_costs += aws_costs
    # azure_costs, _ = azure_adapter.get_azure_costs()
    # all_costs += azure_costs

    if provider:
        all_costs = [c for c in all_costs if c.provider == provider]

    return all_costs


def get_cost_summary() -> CostSummary:
    costs = get_all_costs()

    by_provider: dict[str, float] = {}
    for c in costs:
        by_provider[c.provider] = round(by_provider.get(c.provider, 0.0) + c.amount_usd, 2)

    total = round(sum(by_provider.values()), 2)

    return CostSummary(
        total_usd=total,
        by_provider=by_provider,
        as_of=datetime.now(timezone.utc).isoformat(),
    )


def get_provider_statuses() -> list[ProviderStatus]:
    statuses = []

    _, gcp_resource_source = gcp_adapter.get_gcp_resources()
    _, gcp_cost_source = gcp_adapter.get_gcp_costs()
    statuses.append(
        ProviderStatus(
            provider="gcp",
            resources_source=gcp_resource_source,
            cost_source=gcp_cost_source,
        )
    )

    # Same pattern to be added for aws / azure once those adapters exist.

    return statuses
