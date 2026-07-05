# Software Requirements Specification (SRS)
## Multi-Cloud Unified Dashboard — Hackathon MVP

**Version:** 1.0
**Status:** Draft for Hackathon Build
**Stack:** FastAPI (backend) · Next.js + Tailwind CSS (frontend)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for a hackathon MVP that unifies resource inventory and cost data from AWS, GCP, and Azure into a single dashboard.

### 1.2 Scope
The system will:
- Fetch cloud resources (compute, storage, database, network) from AWS, GCP, and Azure.
- Fetch cost/billing data from each cloud's native cost API.
- Normalize both into a single unified schema.
- Present them in a single web dashboard with combined and per-cloud cost views.

**Out of scope for this MVP:**
- Write/provisioning actions (create, modify, delete resources).
- Real-time streaming updates (polling/on-demand refresh only).
- Multi-tenant auth, RBAC, or user management.
- Alerting, anomaly detection, or budget automation.
- Persistent long-term historical storage (in-memory or SQLite only).

### 1.3 Intended Audience
Hackathon judges, teammates, and future contributors extending the project post-hackathon.

### 1.4 Definitions
| Term | Meaning |
|---|---|
| IDP | Internal Developer Platform |
| Unified Schema | Common JSON shape all cloud resources/costs are normalized into |
| Adapter | Module responsible for translating one cloud's native API response into the Unified Schema |

---

## 2. Overall Description

### 2.1 Product Perspective
A standalone, read-only aggregation dashboard. Not a replacement for each cloud's native console — it is a normalization and visualization layer on top of existing cloud APIs.

### 2.2 User Classes
- **Primary user:** Developer/DevOps engineer who wants a single view of resources and spend across clouds.
- **Demo user (hackathon):** Judge evaluating the working product.

### 2.3 Operating Environment
- Backend: Python 3.11+, FastAPI, deployed locally or on a single container.
- Frontend: Next.js 14+, Tailwind CSS, served locally via `npm run dev` or built for static hosting.
- Cloud credentials: Local CLI-based credentials (`aws configure`, `gcloud auth application-default login`, `az login`) or service account / service principal keys supplied via `.env`.

### 2.4 Assumptions & Dependencies
- Test accounts on all three clouds already exist and have Cost Explorer / Cloud Billing / Cost Management enabled **before** development starts.
- Network access to `api.anthropic.com` is not required for this feature; cloud SDK calls go directly to AWS/GCP/Azure endpoints.
- If live credentials are unavailable during development or demo, the system falls back to seeded mock JSON per provider.

---

## 3. System Features / Functional Requirements

### FR-1: Resource Inventory Fetch
- FR-1.1: System shall fetch compute, storage, database, and network resources from AWS via `boto3` (EC2, S3, RDS at minimum).
- FR-1.2: System shall fetch equivalent resources from GCP via `google-cloud-*` SDKs (Compute Engine, Cloud Storage, Cloud SQL).
- FR-1.3: System shall fetch equivalent resources from Azure via `azure-mgmt-*` SDKs (Virtual Machines, Storage Accounts, Azure SQL).
- FR-1.4: Each adapter shall map its native response into the Unified Resource Schema (see SRS §6).
- FR-1.5: If a live API call fails or credentials are missing, the adapter shall return seeded mock data for that provider and flag `"source": "mock"`.

### FR-2: Cost Data Fetch
- FR-2.1: System shall fetch cost/usage data from AWS Cost Explorer API (`GetCostAndUsage`).
- FR-2.2: System shall fetch cost/usage data from GCP Cloud Billing API.
- FR-2.3: System shall fetch cost/usage data from Azure Cost Management API (Query endpoint).
- FR-2.4: Cost data shall be grouped by service/resource type per cloud at minimum; per-resource attribution is best-effort (dependent on tagging).
- FR-2.5: System shall aggregate all three providers' costs into a single combined total (month-to-date and/or forecast).

### FR-3: Normalization Layer
- FR-3.1: All adapters output data conforming strictly to the Unified Schema.
- FR-3.2: A normalization service merges all provider outputs into one in-memory (or SQLite-backed) store per session/request.

### FR-4: API Layer (FastAPI)
- FR-4.1: `GET /api/resources` — returns unified resource list, optional query params: `provider`, `type`, `region`.
- FR-4.2: `GET /api/costs` — returns unified cost breakdown, optional query params: `provider`, `granularity`.
- FR-4.3: `GET /api/costs/summary` — returns single combined total + per-provider subtotal.
- FR-4.4: `GET /api/health` — returns adapter status per provider (`live` / `mock` / `error`).

### FR-5: Dashboard UI (Next.js + Tailwind)
- FR-5.1: Landing view shows a summary card: total estimated/actual monthly spend across all clouds.
- FR-5.2: Donut/bar chart showing per-cloud cost breakdown.
- FR-5.3: Resource table/grid, filterable by provider and resource type.
- FR-5.4: Per-provider status indicator (live data vs. mock fallback) shown in the UI, not hidden — important for demo transparency.
- FR-5.5: Loading and empty states for all data-fetching views.

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Dashboard initial load shall render within 3 seconds using seeded/mock data. |
| NFR-2 | System must degrade gracefully — a failure in one cloud adapter must not block the other two from rendering. |
| NFR-3 | No cloud credentials shall be hardcoded in source; all secrets via `.env` (excluded from version control). |
| NFR-4 | Code shall be organized so each cloud adapter is independently swappable/testable. |
| NFR-5 | UI must be responsive down to a standard laptop viewport (demo projector safe: 1280×720 minimum). |

---

## 5. External Interface Requirements

### 5.1 AWS
- SDK: `boto3`
- APIs: EC2 (`describe_instances`), S3 (`list_buckets`), RDS (`describe_db_instances`), Cost Explorer (`GetCostAndUsage`)
- Auth: IAM user/role with `ReadOnlyAccess` + `ce:GetCostAndUsage` permission

### 5.2 GCP
- SDK: `google-cloud-compute`, `google-cloud-storage`, `google-cloud-billing`
- Auth: Service account JSON key with Viewer + Billing Account Viewer roles

### 5.3 Azure
- SDK: `azure-mgmt-compute`, `azure-mgmt-storage`, `azure-mgmt-costmanagement`
- Auth: Service principal (Client ID, Tenant ID, Client Secret) with Reader + Cost Management Reader roles

---

## 6. Unified Data Schemas

### 6.1 Unified Resource Schema
```json
{
  "id": "aws-i-0123abcd",
  "provider": "aws",
  "type": "compute",
  "name": "web-server-prod",
  "region": "us-east-1",
  "status": "running",
  "tags": { "env": "prod", "team": "platform" },
  "source": "live",
  "raw": {}
}
```

### 6.2 Unified Cost Schema
```json
{
  "provider": "aws",
  "service": "EC2",
  "granularity": "MONTHLY",
  "period_start": "2026-07-01",
  "period_end": "2026-07-31",
  "amount_usd": 142.37,
  "type": "actual",
  "source": "live"
}
```

### 6.3 Cost Summary Response
```json
{
  "total_usd": 412.90,
  "by_provider": {
    "aws": 142.37,
    "gcp": 118.20,
    "azure": 152.33
  },
  "as_of": "2026-07-04T00:00:00Z"
}
```

---

## 7. Constraints
- 3-hour development window — architecture favors speed and demo reliability over completeness or production hardening.
- No provisioning/write operations permitted against any cloud account.
- Cost data accuracy is bound by each provider's native billing latency (AWS Cost Explorer data can lag; GCP/Azure similar).

---

## 8. Future Considerations (Post-Hackathon, Not in MVP)
- Persistent database + historical trend charts.
- Budget alerts / anomaly detection.
- Tag-enforcement and per-resource cost attribution.
- SSO / multi-user auth.
- Provisioning via Crossplane/Terraform integration.
