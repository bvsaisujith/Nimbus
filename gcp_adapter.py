"""
GCP Adapter.

Responsible for:
1. Fetching GCP resources (Compute Engine instances, Cloud Storage buckets,
   Cloud SQL instances) and mapping them to UnifiedResource.
2. Fetching GCP cost data and mapping it to UnifiedCostEntry.
3. Falling back to mocks/gcp_mock.json if credentials are missing or any
   live call fails — this must never raise up to the router layer.

Cost data note (read this before debugging "why is cost always mock"):
GCP's Cloud Billing API does not expose actual historical spend directly.
Real spend requires BigQuery Billing Export to be enabled in the GCP console
(Billing > Billing export > BigQuery export), which writes a queryable table.
If GCP_BILLING_BQ_TABLE is not set in .env, this adapter intentionally skips
the live cost path and returns mock cost data — this is expected MVP behavior,
not a bug.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path

from schemas.unified import UnifiedResource, UnifiedCostEntry, DataSource

MOCK_PATH = Path(__file__).parent.parent / "mocks" / "gcp_mock.json"


def _load_mock() -> dict:
    with open(MOCK_PATH, "r") as f:
        return json.load(f)


def _get_credentials_and_project():
    """
    Returns (credentials, project_id) or (None, None) if not configured.
    Isolated so both resource and cost fetchers can reuse it.
    """
    from google.oauth2 import service_account

    key_path = os.getenv("GCP_SERVICE_ACCOUNT_JSON_PATH")
    project_id = os.getenv("GCP_PROJECT_ID")

    if not key_path or not project_id or not os.path.exists(key_path):
        return None, None

    credentials = service_account.Credentials.from_service_account_file(key_path)
    return credentials, project_id


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

def get_gcp_resources() -> tuple[list[UnifiedResource], DataSource]:
    """
    Returns (list_of_resources, source) where source is 'live' or 'mock'.
    Never raises — any failure falls back to mock data.
    """
    credentials, project_id = _get_credentials_and_project()
    if not credentials:
        return _mock_resources(), "mock"

    try:
        resources: list[UnifiedResource] = []
        resources += _fetch_compute_instances(credentials, project_id)
        resources += _fetch_storage_buckets(credentials, project_id)
        resources += _fetch_cloudsql_instances(credentials, project_id)

        if not resources:
            # Live call succeeded but account is empty — still "live", just no data.
            return [], "live"

        return resources, "live"

    except Exception as e:
        print(f"[gcp_adapter] Live resource fetch failed, falling back to mock: {e}")
        return _mock_resources(), "mock"


def _mock_resources() -> list[UnifiedResource]:
    data = _load_mock()
    return [UnifiedResource(**r) for r in data["resources"]]


def _fetch_compute_instances(credentials, project_id) -> list[UnifiedResource]:
    from google.cloud import compute_v1

    client = compute_v1.InstancesClient(credentials=credentials)
    agg_request = compute_v1.AggregatedListInstancesRequest(project=project_id)
    results = []

    for zone, response in client.aggregated_list(request=agg_request):
        if not response.instances:
            continue
        zone_name = zone.split("/")[-1]
        for instance in response.instances:
            results.append(
                UnifiedResource(
                    id=f"gcp-instance-{instance.name}",
                    provider="gcp",
                    type="compute",
                    name=instance.name,
                    region=zone_name,
                    status=instance.status,
                    tags=dict(instance.labels) if instance.labels else {},
                    source="live",
                    raw={},
                )
            )
    return results


def _fetch_storage_buckets(credentials, project_id) -> list[UnifiedResource]:
    from google.cloud import storage

    client = storage.Client(project=project_id, credentials=credentials)
    results = []

    for bucket in client.list_buckets():
        results.append(
            UnifiedResource(
                id=f"gcp-bucket-{bucket.name}",
                provider="gcp",
                type="storage",
                name=bucket.name,
                region=bucket.location or "unknown",
                status="ACTIVE",
                tags=bucket.labels or {},
                source="live",
                raw={},
            )
        )
    return results


def _fetch_cloudsql_instances(credentials, project_id) -> list[UnifiedResource]:
    from googleapiclient.discovery import build

    service = build("sqladmin", "v1beta4", credentials=credentials)
    request = service.instances().list(project=project_id)
    results = []

    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            results.append(
                UnifiedResource(
                    id=f"gcp-sql-{item['name']}",
                    provider="gcp",
                    type="database",
                    name=item["name"],
                    region=item.get("region", "unknown"),
                    status=item.get("state", "UNKNOWN"),
                    tags={},
                    source="live",
                    raw={},
                )
            )
        request = service.instances().list_next(
            previous_request=request, previous_response=response
        )
    return results


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------

def get_gcp_costs() -> tuple[list[UnifiedCostEntry], DataSource]:
    """
    Returns (list_of_cost_entries, source) where source is 'live' or 'mock'.
    Requires GCP_BILLING_BQ_TABLE to attempt live data (see module docstring).
    """
    bq_table = os.getenv("GCP_BILLING_BQ_TABLE")
    credentials, project_id = _get_credentials_and_project()

    if not bq_table or not credentials:
        return _mock_costs(), "mock"

    try:
        return _fetch_bigquery_costs(credentials, project_id, bq_table), "live"
    except Exception as e:
        print(f"[gcp_adapter] Live cost fetch failed, falling back to mock: {e}")
        return _mock_costs(), "mock"


def _mock_costs() -> list[UnifiedCostEntry]:
    data = _load_mock()
    return [UnifiedCostEntry(**c) for c in data["costs"]]


def _fetch_bigquery_costs(credentials, project_id, bq_table: str) -> list[UnifiedCostEntry]:
    from google.cloud import bigquery

    client = bigquery.Client(project=project_id, credentials=credentials)

    today = date.today()
    period_start = today.replace(day=1)

    query = f"""
        SELECT
          service.description AS service_name,
          SUM(cost) AS total_cost
        FROM `{bq_table}`
        WHERE DATE(usage_start_time) >= @period_start
        GROUP BY service_name
        ORDER BY total_cost DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("period_start", "DATE", period_start),
        ]
    )

    rows = client.query(query, job_config=job_config).result()

    entries = []
    for row in rows:
        entries.append(
            UnifiedCostEntry(
                provider="gcp",
                service=row.service_name,
                granularity="MONTHLY",
                period_start=period_start.isoformat(),
                period_end=today.isoformat(),
                amount_usd=round(float(row.total_cost), 2),
                type="actual",
                source="live",
            )
        )
    return entries
