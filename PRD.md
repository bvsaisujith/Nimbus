# Product Requirements Document (PRD)
## Multi-Cloud Unified Dashboard — Hackathon MVP

**Version:** 1.0
**Status:** Draft for Hackathon Build
**Stack:** FastAPI (backend) · Next.js + Tailwind CSS (frontend)

---

## 1. Problem Statement

Teams running workloads across AWS, GCP, and Azure have no single place to see what resources exist and what they cost. Engineers bounce between three consoles, and no one has a fast answer to "what are we spending across all clouds right now?" This MVP proves that a unified view is achievable quickly, using each cloud's own resource and cost APIs.

## 2. Goal / Vision

Build a read-only dashboard that:
1. Pulls live (or mock-fallback) resource inventory from AWS, GCP, and Azure.
2. Pulls live (or mock-fallback) cost data from each cloud's native cost API.
3. Normalizes everything into one schema.
4. Displays it in a single, clean, judge-friendly dashboard within a 3-hour build window.

## 3. Target User

Primary persona: **Platform/DevOps engineer** who wants a fast, unified snapshot of multi-cloud spend and inventory without opening three separate consoles.

Hackathon persona: **Judge** evaluating whether the demo proves the core "unification" concept convincingly.

## 4. Success Metrics (Hackathon Context)

| Metric | Target |
|---|---|
| Demo runs end-to-end without crashing | Required |
| At least 1 cloud shows live (non-mock) data | Required |
| Combined cost total renders correctly | Required |
| Resource table filters by provider/type | Required |
| Judges understand the unification value in <60 sec | Required |

## 5. Scope

### 5.1 In Scope (MVP — 3 hours)
- Read-only resource fetch: AWS, GCP, Azure (compute, storage, database at minimum)
- Read-only cost fetch: AWS Cost Explorer, GCP Cloud Billing, Azure Cost Management
- Unified schema + normalization layer
- FastAPI backend exposing unified REST endpoints
- Next.js + Tailwind dashboard: summary cost card, per-cloud breakdown chart, resource table with filters
- Mock-data fallback per provider if credentials/API calls fail

### 5.2 Out of Scope (MVP)
- Any provisioning, modification, or deletion of cloud resources
- User authentication / multi-tenancy
- Persistent database beyond SQLite/in-memory
- Real-time push updates (polling/manual refresh only)
- Budget alerts, anomaly detection, cost optimization recommendations
- Per-resource cost attribution beyond what native tagging already supports

## 6. User Stories

- **As a platform engineer**, I want to see all my cloud resources in one table, so I don't have to check three consoles.
- **As a platform engineer**, I want to see my combined monthly cloud spend as a single number, so I can quickly gauge overall burn.
- **As a platform engineer**, I want to filter resources by cloud provider or type, so I can drill into a specific area.
- **As a judge**, I want to clearly see that data is being pulled from real cloud APIs (or transparently marked as mock), so I can trust the demo.

## 7. Functional Requirements Summary

(Full detail in SRS §3)

1. Fetch + normalize resources from 3 clouds.
2. Fetch + normalize cost data from 3 clouds' native cost APIs.
3. Expose unified REST API via FastAPI.
4. Render dashboard: summary card, cost breakdown chart, filterable resource table.
5. Gracefully fall back to mock data per-provider on failure, with visible status indicator.

## 8. Non-Goals

This is explicitly **not**:
- A full IDP or provisioning platform (that's the larger post-hackathon vision).
- A production-grade cost management / FinOps tool.
- A tool with write access to any cloud account.

## 9. Assumptions

- All three cloud accounts used in the demo have billing APIs already enabled (AWS Cost Explorer must be manually enabled and takes ~24h to populate — must be done before hackathon starts).
- Local developer machine has CLI credentials already configured for at least one cloud, ideally all three.
- Judges will accept "mock fallback, clearly labeled" as a legitimate MVP answer for any cloud where live credentials aren't available on demo day.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Cost Explorer/Billing API not enabled in time | Enable all three before hackathon starts; verify with a test call |
| OAuth/IAM setup eats the clock | Use existing local CLI credentials instead of building auth UI |
| One cloud's live call fails mid-demo | Adapter-level fallback to seeded mock JSON, never blocks other two |
| Scope creep (adding provisioning, alerts, etc.) | Hard cutoff per SRS §2.2 "Out of scope" — do not touch during build |

## 11. Timeline (3-Hour Build)

| Time | Milestone |
|---|---|
| 0:00–0:20 | Confirm schema, confirm credential strategy, scaffold repo |
| 0:20–1:15 | Build 3 provider adapters (resources + cost), unified schema, tested via console/logs |
| 1:15–1:30 | Cost aggregation endpoint |
| 1:30–2:20 | Dashboard UI: summary card, chart, resource table + filters |
| 2:20–2:45 | Polish: loading/empty states, mock fallback wiring, status indicators |
| 2:45–3:00 | Demo rehearsal, README finalization |

## 12. Open Questions

- Do we want per-resource cost estimates (best-effort via tags) in the MVP, or is per-service/per-cloud breakdown sufficient? (Current recommendation: per-service/per-cloud only, for time reasons.)
- Which cloud gets guaranteed live data if only one can be fully set up before the hackathon?
