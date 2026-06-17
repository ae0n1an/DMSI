# ServiceNow XLSX Data Source — Design Spec

**Date:** 2026-06-17
**Status:** Approved

---

## Overview

Add a persistent, xlsx-backed data source for ServiceNow data. Users upload an exported ServiceNow xlsx file once; it is stored in SQLite and queried by the chatbot from then on. The existing API integration is preserved as a future upgrade path.

---

## Goals

- Ingest a ServiceNow xlsx export and store it persistently in SQLite
- Answer natural language queries against that data (priority summary, stage times, ticket lookup, filtered lists, ad-hoc SQL)
- Render charts for priority breakdown (L1–L4) and time-in-stage metrics
- Give the developer a UI to re-upload data; regular users never see the upload control
- Keep the existing ServiceNow API plumbing intact for future use

---

## Storage — `data/servicenow.db`

- SQLite database at `data/servicenow.db` (added to `.gitignore`)
- Table: `incidents` — one row per ticket, columns normalized from xlsx headers
- Table: `upload_log` — filename, row count, uploaded_at timestamp

### Column normalisation

xlsx headers are lowercased and spaces replaced with underscores. Key mappings:

| xlsx header | db column |
|---|---|
| Number | number |
| Short Description | short_description |
| Priority | priority (integer 1–4) |
| State | state |
| Created | created_at |
| Work start | work_start |
| Closed | closed_at |
| Business duration | business_duration |
| Assignment group | assignment_group |
| Assigned to | assigned_to |
| Tags | tags |
| Description | description |
| Due date | due_date |
| Active | active |
| Raised for | raised_for |
| Resolution notes | resolution_notes |
| Configuration item | configuration_item |
| Impact | impact |
| Urgency | urgency |

All remaining columns are stored as-is (snake_case names).

### Ingestion behaviour

On upload: read xlsx with pandas → normalize columns → `DELETE FROM incidents` → bulk insert → append row to `upload_log`. Replaces all existing data.

Column mapping is lenient: known columns are mapped to their normalized names; unknown columns are stored as snake_case versions of their header; missing expected columns are stored as NULL rather than raising an error.

---

## Data Layer — `chatbot/integrations/servicenow_store.py`

New module. Provides:

- `is_loaded() -> bool` — True if `incidents` table has rows
- `get_incidents(state, priority, assignment_group, limit) -> list[dict]`
- `get_priority_summary() -> dict` — counts by priority × state
- `get_stage_times() -> dict` — average days: queue time (created_at → work_start), resolution time (work_start → closed_at), total time (created_at → closed_at), per priority
- `get_ticket(number) -> dict | None`
- `run_sql(sql) -> list[dict]` — read-only; rejects any statement that isn't SELECT

`servicenow_client.py` updated: `get_incidents()`, `get_incident()`, `get_stats()` each check `servicenow_store.is_loaded()` first and delegate to the store; fall back to API (then mock) if store is empty.

---

## LangChain Tools — `chatbot/tools/servicenow_tools.py`

Five tools (replaces the current three; existing tool names kept where possible):

| Tool | Description |
|---|---|
| `get_servicenow_priority_summary` | Ticket counts grouped by L1–L4, broken down by state |
| `get_servicenow_stage_times` | Average queue time, resolution time, total time per priority level |
| `get_servicenow_ticket(number)` | Full details for a single ticket by ID (e.g. INC100001) |
| `get_servicenow_tickets` | Filtered list: priority, state, assignment_group, date range, limit |
| `query_servicenow_sql(sql)` | Fallback: run a read-only SQL query; tool description includes db schema |

The `query_servicenow_sql` tool description embeds the column list so the LLM can write correct SQL without hallucinating column names.

---

## Charts — `chatbot/visualizations/charts.py`

Two new chart builders added:

- **`priority_summary_bar`** — grouped bar chart: L1/L2/L3/L4 on x-axis, count on y-axis, bars coloured by state (open/in progress/resolved)
- **`stage_time_bar`** — bar chart: stage (queue / resolution / total) on x-axis, average days on y-axis, grouped by priority

Existing chart types unchanged.

---

## UI — `chatbot/app.py` + sidebar

**Sidebar additions:**

- "Last loaded" caption always visible: shows filename, row count, and upload date from `upload_log`. Shows "No data loaded" if store is empty.
- File uploader (`st.file_uploader`, `.xlsx` only) shown only when `DEV_MODE=true` env var is set. On successful upload shows row count; on error shows the exception message.

**System prompt update:**

Add a sentence noting that ServiceNow data is loaded from an xlsx export and that the agent has tools for priority summary and stage time analysis.

---

## Environment & Files

| Change | Detail |
|---|---|
| `data/servicenow.db` | New SQLite file, gitignored |
| `chatbot/integrations/servicenow_store.py` | New module |
| `chatbot/integrations/servicenow_client.py` | Updated: store-first fallback |
| `chatbot/tools/servicenow_tools.py` | Updated: 5 tools |
| `chatbot/visualizations/charts.py` | Updated: 2 new chart types |
| `chatbot/app.py` | Updated: sidebar upload UI, system prompt |
| `chatbot/requirements.txt` | Add `pandas>=2.0.0` and `openpyxl>=3.1.0` (xlsx parsing) |
| `.gitignore` | Add `data/` |

---

## Out of Scope

- Multi-file uploads / merging data from multiple exports
- User-facing upload (upload is dev-only)
- Real-time sync with ServiceNow API
- Authentication / access control on the upload UI
