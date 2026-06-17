# ServiceNow XLSX Data Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent SQLite-backed data source for ServiceNow xlsx exports so the chatbot can answer queries and render charts from uploaded data.

**Architecture:** An xlsx file is uploaded via a dev-only sidebar widget, parsed with pandas, and stored in `data/servicenow.db`. A new `servicenow_store.py` module handles all SQLite reads. `servicenow_client.py` is updated to check the store first, falling back to the API/mock. Five focused LangChain tools (priority summary, stage times, ticket lookup, filtered list, ad-hoc SQL) replace the existing three. Two new Plotly chart types (priority bar, stage time bar) are added.

**Tech Stack:** Python 3.11+, pandas, openpyxl, sqlite3 (stdlib), Plotly, LangChain, Streamlit

## Global Constraints

- All tests run from `chatbot/` directory: `cd chatbot && pytest tests/`
- Test imports use `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))` pattern (match existing tests)
- `USE_MOCK_DATA=true` env var in test files (match existing pattern)
- Priority is always stored as integer 1–4 in SQLite; ingestion extracts leading digit from strings like "1 - Critical"
- `data/servicenow.db` is gitignored; `data/` dir is created at runtime if absent
- DEV_MODE upload UI gated on `os.getenv("DEV_MODE", "false").lower() == "true"`
- Never break existing tests — existing tool names `get_servicenow_incidents`, `get_servicenow_incident`, `get_servicenow_stats` are removed and replaced; update the count assertion in `test_servicenow_tools.py`

---

### Task 1: Dependencies, .gitignore, data directory

**Files:**
- Modify: `chatbot/requirements.txt`
- Create: `.gitignore`

**Interfaces:**
- Produces: nothing consumed by code — environment setup only

- [ ] **Step 1: Add pandas and openpyxl to requirements.txt**

Open `chatbot/requirements.txt` and add two lines after the existing entries:

```
pandas>=2.0.0
openpyxl>=3.1.0
```

Final file:
```
streamlit>=1.35.0
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
langchain-community>=0.2.0
openai>=1.30.0
plotly>=5.20.0
python-dotenv>=1.0.0
requests>=2.31.0
slack-sdk>=3.27.0
pytest>=8.0.0
pandas>=2.0.0
openpyxl>=3.1.0
```

- [ ] **Step 2: Create .gitignore at repo root**

Create `/Users/maxverhoef/ClaudeProjects/streamlit-chatbot/.gitignore`:

```
data/
__pycache__/
*.pyc
.env
.pytest_cache/
```

- [ ] **Step 3: Install new dependencies**

```bash
pip install pandas>=2.0.0 openpyxl>=3.1.0
```

Expected: both packages install without error.

- [ ] **Step 4: Commit**

```bash
git add chatbot/requirements.txt .gitignore
git commit -m "chore: add pandas/openpyxl deps and gitignore data dir"
```

---

### Task 2: `servicenow_store.py` — SQLite store

**Files:**
- Create: `chatbot/integrations/servicenow_store.py`
- Create: `chatbot/tests/test_servicenow_store.py`

**Interfaces:**
- Produces:
  - `DB_PATH: str` — module-level path to SQLite file (patchable in tests)
  - `is_loaded() -> bool`
  - `load_xlsx(file_bytes: bytes, filename: str) -> int` — returns row count
  - `get_last_upload() -> dict | None` — keys: filename, row_count, uploaded_at
  - `get_incidents(state=None, priority=None, assignment_group=None, limit=100) -> list[dict]`
  - `get_priority_summary() -> dict` — `{1: {"open": 3, "resolved": 2}, 2: {...}, ...}`
  - `get_stage_times() -> dict` — `{1: {"queue_days": 2.5, "resolution_days": 5.0, "total_days": 7.5}, ...}`
  - `get_ticket(number: str) -> dict | None`
  - `run_sql(sql: str) -> list[dict]` — raises ValueError for non-SELECT

- [ ] **Step 1: Write the failing tests**

Create `chatbot/tests/test_servicenow_store.py`:

```python
import io
import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import integrations.servicenow_store as store


def _make_xlsx(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


_SAMPLE_ROWS = [
    {
        "Number": "INC000001",
        "Short Description": "Network down",
        "Priority": "1 - Critical",
        "State": "open",
        "Created": "2026-01-01 09:00:00",
        "Work start": "2026-01-01 10:00:00",
        "Closed": "2026-01-02 09:00:00",
        "Assignment group": "Network Ops",
        "Assigned to": "alice",
        "Tags": "network",
    },
    {
        "Number": "INC000002",
        "Short Description": "Slow login",
        "Priority": "2 - High",
        "State": "resolved",
        "Created": "2026-01-03 08:00:00",
        "Work start": "2026-01-03 09:00:00",
        "Closed": "2026-01-04 08:00:00",
        "Assignment group": "Service Desk",
        "Assigned to": "bob",
        "Tags": "auth",
    },
    {
        "Number": "INC000003",
        "Short Description": "Printer offline",
        "Priority": "4 - Low",
        "State": "open",
        "Created": "2026-01-05 07:00:00",
        "Work start": None,
        "Closed": None,
        "Assignment group": "Network Ops",
        "Assigned to": None,
        "Tags": None,
    },
]


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test.db"))


def test_is_loaded_false_when_empty():
    assert store.is_loaded() is False


def test_load_xlsx_returns_row_count():
    count = store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    assert count == 3


def test_is_loaded_true_after_load():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    assert store.is_loaded() is True


def test_load_xlsx_normalises_priority():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.get_incidents()
    priorities = {r["number"]: r["priority"] for r in rows}
    assert priorities["INC000001"] == 1
    assert priorities["INC000002"] == 2
    assert priorities["INC000003"] == 4


def test_get_last_upload():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "myfile.xlsx")
    info = store.get_last_upload()
    assert info is not None
    assert info["filename"] == "myfile.xlsx"
    assert info["row_count"] == 3


def test_get_incidents_all():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.get_incidents()
    assert len(rows) == 3


def test_get_incidents_filter_state():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.get_incidents(state="open")
    assert len(rows) == 2
    assert all(r["state"] == "open" for r in rows)


def test_get_incidents_filter_priority():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.get_incidents(priority=1)
    assert len(rows) == 1
    assert rows[0]["number"] == "INC000001"


def test_get_incidents_filter_assignment_group():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.get_incidents(assignment_group="Network Ops")
    assert len(rows) == 2


def test_get_priority_summary():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    summary = store.get_priority_summary()
    assert summary[1]["open"] == 1
    assert summary[2]["resolved"] == 1
    assert summary[4]["open"] == 1


def test_get_stage_times_returns_dict_per_priority():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    times = store.get_stage_times()
    assert 1 in times
    assert "queue_days" in times[1]
    assert "resolution_days" in times[1]
    assert "total_days" in times[1]


def test_get_stage_times_queue_days_correct():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    times = store.get_stage_times()
    # INC000001: work_start - created_at = 1 hour = 1/24 days ≈ 0.04
    assert times[1]["queue_days"] is not None
    assert times[1]["queue_days"] < 0.1


def test_get_ticket_found():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    ticket = store.get_ticket("INC000001")
    assert ticket is not None
    assert ticket["short_description"] == "Network down"


def test_get_ticket_not_found():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    assert store.get_ticket("INC999999") is None


def test_run_sql_select():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    rows = store.run_sql("SELECT number FROM incidents WHERE priority = 1")
    assert len(rows) == 1
    assert rows[0]["number"] == "INC000001"


def test_run_sql_rejects_non_select():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "test.xlsx")
    with pytest.raises(ValueError, match="Only SELECT"):
        store.run_sql("DELETE FROM incidents")


def test_load_xlsx_replaces_existing_data():
    store.load_xlsx(_make_xlsx(_SAMPLE_ROWS), "first.xlsx")
    new_rows = [_SAMPLE_ROWS[0]]
    store.load_xlsx(_make_xlsx(new_rows), "second.xlsx")
    assert len(store.get_incidents()) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_store.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'integrations.servicenow_store'`

- [ ] **Step 3: Implement `servicenow_store.py`**

Create `chatbot/integrations/servicenow_store.py`:

```python
import io
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servicenow.db")

_COLUMN_MAP = {
    "number": "number",
    "short description": "short_description",
    "priority": "priority",
    "state": "state",
    "created": "created_at",
    "work start": "work_start",
    "closed": "closed_at",
    "business duration": "business_duration",
    "assignment group": "assignment_group",
    "assigned to": "assigned_to",
    "tags": "tags",
    "description": "description",
    "due date": "due_date",
    "active": "active",
    "raised for": "raised_for",
    "resolution notes": "resolution_notes",
    "configuration item": "configuration_item",
    "impact": "impact",
    "urgency": "urgency",
}


def _normalize_col(header: str) -> str:
    lower = header.lower().strip()
    return _COLUMN_MAP.get(lower, re.sub(r"\s+", "_", lower))


def _normalize_priority(val) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    m = re.match(r"^(\d+)", str(val).strip())
    return int(m.group(1)) if m else None


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_upload_log(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            row_count INTEGER,
            uploaded_at TEXT
        )
        """
    )
    conn.commit()


def is_loaded() -> bool:
    try:
        with _conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM incidents")
            return cur.fetchone()[0] > 0
    except Exception:
        return False


def load_xlsx(file_bytes: bytes, filename: str) -> int:
    df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    df.columns = [_normalize_col(c) for c in df.columns]
    if "priority" in df.columns:
        df["priority"] = df["priority"].apply(_normalize_priority)
    row_count = len(df)
    with _conn() as conn:
        _ensure_upload_log(conn)
        df.to_sql("incidents", conn, if_exists="replace", index=False)
        conn.execute(
            "INSERT INTO upload_log (filename, row_count, uploaded_at) VALUES (?, ?, ?)",
            (filename, row_count, datetime.utcnow().isoformat()),
        )
        conn.commit()
    return row_count


def get_last_upload() -> dict | None:
    try:
        with _conn() as conn:
            _ensure_upload_log(conn)
            cur = conn.execute(
                "SELECT filename, row_count, uploaded_at FROM upload_log ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def get_incidents(
    state: str | None = None,
    priority: int | None = None,
    assignment_group: str | None = None,
    limit: int = 100,
) -> list[dict]:
    conditions, params = [], []
    if state:
        conditions.append("state = ?")
        params.append(state)
    if priority is not None:
        conditions.append("priority = ?")
        params.append(priority)
    if assignment_group:
        conditions.append("assignment_group = ?")
        params.append(assignment_group)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    try:
        with _conn() as conn:
            cur = conn.execute(f"SELECT * FROM incidents {where} LIMIT ?", params)
            return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def get_priority_summary() -> dict:
    try:
        with _conn() as conn:
            cur = conn.execute(
                "SELECT priority, state, COUNT(*) as cnt FROM incidents GROUP BY priority, state"
            )
            result: dict = {}
            for row in cur.fetchall():
                p = row["priority"]
                s = str(row["state"]).lower() if row["state"] else "unknown"
                if p not in result:
                    result[p] = {}
                result[p][s] = row["cnt"]
            return result
    except Exception:
        return {}


def get_stage_times() -> dict:
    try:
        with _conn() as conn:
            df = pd.read_sql(
                "SELECT priority, created_at, work_start, closed_at FROM incidents", conn
            )
        for col in ("created_at", "work_start", "closed_at"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df["queue_days"] = (df["work_start"] - df["created_at"]).dt.total_seconds() / 86400
        df["resolution_days"] = (df["closed_at"] - df["work_start"]).dt.total_seconds() / 86400
        df["total_days"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 86400
        result = {}
        for priority, grp in df.groupby("priority"):
            result[int(priority)] = {
                "queue_days": _safe_mean(grp["queue_days"]),
                "resolution_days": _safe_mean(grp["resolution_days"]),
                "total_days": _safe_mean(grp["total_days"]),
            }
        return result
    except Exception:
        return {}


def _safe_mean(series: "pd.Series") -> float | None:
    valid = series.dropna()
    return round(float(valid.mean()), 2) if not valid.empty else None


def get_ticket(number: str) -> dict | None:
    try:
        with _conn() as conn:
            cur = conn.execute(
                "SELECT * FROM incidents WHERE number = ? LIMIT 1", (number,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def run_sql(sql: str) -> list[dict]:
    stripped = sql.strip().lstrip(";").strip().upper()
    if not stripped.startswith("SELECT"):
        raise ValueError("Only SELECT statements are permitted.")
    try:
        with _conn() as conn:
            cur = conn.execute(sql)
            return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error as exc:
        raise ValueError(f"SQL error: {exc}") from exc
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_store.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add chatbot/integrations/servicenow_store.py chatbot/tests/test_servicenow_store.py
git commit -m "feat: add servicenow_store — SQLite-backed xlsx ingestion and query"
```

---

### Task 3: Update `servicenow_client.py` — store-first routing

**Files:**
- Modify: `chatbot/integrations/servicenow_client.py`
- Modify: `chatbot/tests/test_servicenow_client.py`

**Interfaces:**
- Consumes: `servicenow_store.is_loaded()`, `servicenow_store.get_incidents()`, `servicenow_store.get_ticket()`, `servicenow_store.get_priority_summary()`
- Produces: same public interface as before — `get_incidents()`, `get_incident()`, `get_stats()` — now store-first

- [ ] **Step 1: Read existing test file**

```bash
cat chatbot/tests/test_servicenow_client.py
```

Note any existing test expectations so you don't break them.

- [ ] **Step 2: Write new failing test**

Add to `chatbot/tests/test_servicenow_client.py` (after existing tests):

```python
import unittest.mock as mock

def test_get_incidents_uses_store_when_loaded():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_incidents", return_value=[
             {"number": "INC000001", "short_description": "Store ticket", "state": "open",
              "priority": 1, "assignment_group": "Ops", "created_at": None}
         ]):
        result = servicenow_client.get_incidents()
    assert len(result) == 1
    assert result[0]["number"] == "INC000001"


def test_get_incidents_falls_back_when_store_empty():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=False):
        os.environ["USE_MOCK_DATA"] = "true"
        result = servicenow_client.get_incidents()
    assert len(result) > 0
```

Add the import at the top of the test file if not already present:
```python
import unittest.mock as mock
```

- [ ] **Step 3: Run to verify new tests fail**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_client.py::test_get_incidents_uses_store_when_loaded tests/test_servicenow_client.py::test_get_incidents_falls_back_when_store_empty -v
```

Expected: FAIL — `test_get_incidents_uses_store_when_loaded` will call the API/mock instead of the store.

- [ ] **Step 4: Update `servicenow_client.py`**

Add import at the top of `chatbot/integrations/servicenow_client.py` (after existing imports):

```python
from integrations import servicenow_store
```

Replace the `get_incidents` function:

```python
def get_incidents(state: str | None = None) -> list[dict]:
    if servicenow_store.is_loaded():
        return servicenow_store.get_incidents(state=state)
    if _use_mock():
        return mock_data.get_servicenow_incidents(state)
    try:
        params: dict = {
            "sysparm_limit": 100,
            "sysparm_fields": "number,short_description,state,priority,category,opened_at,resolved_at",
        }
        if state:
            state_map = {"open": "1", "in_progress": "2", "resolved": "6"}
            params["sysparm_query"] = f"state={state_map.get(state, state)}"
        resp = requests.get(
            f"{_base_url()}/api/now/table/incident",
            params=params,
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return [_normalize(r) for r in resp.json().get("result", [])]
    except Exception:
        return mock_data.get_servicenow_incidents(state)
```

Replace the `get_incident` function:

```python
def get_incident(number: str) -> dict | None:
    if servicenow_store.is_loaded():
        return servicenow_store.get_ticket(number)
    if _use_mock():
        return mock_data.get_servicenow_incident(number)
    try:
        resp = requests.get(
            f"{_base_url()}/api/now/table/incident",
            params={"sysparm_query": f"number={number}", "sysparm_limit": 1},
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return _normalize(results[0]) if results else None
    except Exception:
        return mock_data.get_servicenow_incident(number)
```

Replace the `get_stats` function:

```python
def get_stats() -> dict:
    if servicenow_store.is_loaded():
        summary = servicenow_store.get_priority_summary()
        by_priority = {f"P{k}": sum(v.values()) for k, v in summary.items()}
        return {"by_priority": by_priority, "by_category": {}}
    if _use_mock():
        return mock_data.get_servicenow_stats()
    try:
        incidents = get_incidents()
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for inc in incidents:
            p = f"P{inc['priority']}"
            by_priority[p] = by_priority.get(p, 0) + 1
            c = inc["category"]
            by_category[c] = by_category.get(c, 0) + 1
        return {"by_priority": by_priority, "by_category": by_category}
    except Exception:
        return mock_data.get_servicenow_stats()
```

- [ ] **Step 5: Run all servicenow_client tests**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_client.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add chatbot/integrations/servicenow_client.py chatbot/tests/test_servicenow_client.py
git commit -m "feat: update servicenow_client to use store-first routing"
```

---

### Task 4: New LangChain tools + update `chart_tool.py`

**Files:**
- Modify: `chatbot/tools/servicenow_tools.py`
- Modify: `chatbot/tools/chart_tool.py`
- Modify: `chatbot/tests/test_servicenow_tools.py`

**Interfaces:**
- Consumes: `servicenow_store.get_priority_summary()`, `servicenow_store.get_stage_times()`, `servicenow_store.get_incidents()`, `servicenow_store.get_ticket()`, `servicenow_store.run_sql()`; falls back to `servicenow_client.*`
- Produces: `servicenow_tools: list[BaseTool]` with 5 tools; updated `RenderChartInput` Literal with `"priority_summary_bar"` and `"stage_time_bar"`

- [ ] **Step 1: Write failing tests**

Replace the entire contents of `chatbot/tests/test_servicenow_tools.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest.mock as mock
os.environ["USE_MOCK_DATA"] = "true"

from tools.servicenow_tools import (
    get_servicenow_priority_summary,
    get_servicenow_stage_times,
    get_servicenow_ticket,
    get_servicenow_tickets,
    query_servicenow_sql,
    servicenow_tools,
)
from langchain_core.tools import BaseTool


_MOCK_SUMMARY = {
    1: {"open": 3, "resolved": 1},
    2: {"open": 2, "in_progress": 1},
    3: {"resolved": 4},
    4: {"open": 1},
}

_MOCK_STAGE_TIMES = {
    1: {"queue_days": 0.5, "resolution_days": 2.0, "total_days": 2.5},
    2: {"queue_days": 1.0, "resolution_days": 3.0, "total_days": 4.0},
}

_MOCK_INCIDENTS = [
    {"number": "INC000001", "short_description": "Net down", "state": "open",
     "priority": 1, "assignment_group": "Ops", "created_at": "2026-01-01"},
    {"number": "INC000002", "short_description": "Slow login", "state": "resolved",
     "priority": 2, "assignment_group": "Desk", "created_at": "2026-01-02"},
]


def test_priority_summary_returns_string():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_priority_summary", return_value=_MOCK_SUMMARY):
        result = get_servicenow_priority_summary.invoke({})
    assert isinstance(result, str)
    assert "L1" in result


def test_priority_summary_shows_counts():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_priority_summary", return_value=_MOCK_SUMMARY):
        result = get_servicenow_priority_summary.invoke({})
    assert "open: 3" in result or "3" in result


def test_stage_times_returns_string():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_stage_times", return_value=_MOCK_STAGE_TIMES):
        result = get_servicenow_stage_times.invoke({})
    assert isinstance(result, str)
    assert "L1" in result
    assert "queue" in result.lower()


def test_ticket_found():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_ticket", return_value=_MOCK_INCIDENTS[0]):
        result = get_servicenow_ticket.invoke({"number": "INC000001"})
    assert "INC000001" in result


def test_ticket_not_found():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_ticket", return_value=None):
        result = get_servicenow_ticket.invoke({"number": "INC999999"})
    assert "not found" in result.lower()


def test_get_tickets_filtered():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_incidents", return_value=[_MOCK_INCIDENTS[0]]):
        result = get_servicenow_tickets.invoke({"priority": 1, "state": "open"})
    assert "INC000001" in result


def test_get_tickets_empty():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.get_incidents", return_value=[]):
        result = get_servicenow_tickets.invoke({"priority": 1, "state": "open"})
    assert "no tickets" in result.lower()


def test_query_sql_valid():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.run_sql", return_value=[{"number": "INC000001"}]):
        result = query_servicenow_sql.invoke({"sql": "SELECT number FROM incidents LIMIT 1"})
    assert "INC000001" in result


def test_query_sql_error_surfaced():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=True), \
         mock.patch("integrations.servicenow_store.run_sql", side_effect=ValueError("Only SELECT")):
        result = query_servicenow_sql.invoke({"sql": "DELETE FROM incidents"})
    assert "error" in result.lower() or "only select" in result.lower()


def test_query_sql_store_not_loaded():
    with mock.patch("integrations.servicenow_store.is_loaded", return_value=False):
        result = query_servicenow_sql.invoke({"sql": "SELECT number FROM incidents LIMIT 1"})
    assert "no data" in result.lower() or "not loaded" in result.lower()


def test_servicenow_tools_list_has_five_tools():
    assert len(servicenow_tools) == 5
    assert all(isinstance(t, BaseTool) for t in servicenow_tools)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_tools.py -v 2>&1 | head -20
```

Expected: `ImportError` — tools not yet defined.

- [ ] **Step 3: Replace `servicenow_tools.py`**

Replace the entire contents of `chatbot/tools/servicenow_tools.py`:

```python
from langchain_core.tools import tool
from integrations import servicenow_client, servicenow_store

_SCHEMA = (
    "Table: incidents. Key columns: number (TEXT), short_description (TEXT), "
    "priority (INTEGER 1=L1 2=L2 3=L3 4=L4), state (TEXT e.g. open/in_progress/resolved), "
    "created_at (TEXT ISO datetime), work_start (TEXT ISO datetime), closed_at (TEXT ISO datetime), "
    "business_duration (TEXT), assignment_group (TEXT), assigned_to (TEXT), tags (TEXT), "
    "description (TEXT), due_date (TEXT), active (TEXT), raised_for (TEXT), "
    "resolution_notes (TEXT), configuration_item (TEXT), impact (TEXT), urgency (TEXT)."
)


@tool
def get_servicenow_priority_summary() -> str:
    """Get a summary of ServiceNow tickets grouped by priority level (L1/L2/L3/L4) and state."""
    summary = servicenow_store.get_priority_summary()
    if not summary:
        summary_data = servicenow_client.get_stats()
        by_p = summary_data.get("by_priority", {})
        return "\n".join(f"{k}: {v} tickets" for k, v in sorted(by_p.items())) or "No data."
    lines = []
    for priority in sorted(summary.keys()):
        label = f"L{priority}"
        states = summary[priority]
        total = sum(states.values())
        breakdown = ", ".join(f"{s}: {c}" for s, c in sorted(states.items()))
        lines.append(f"{label} — total: {total} ({breakdown})")
    return "\n".join(lines) if lines else "No data."


@tool
def get_servicenow_stage_times() -> str:
    """Get average time spent in each stage (queue time, resolution time, total time) per priority level (L1-L4)."""
    times = servicenow_store.get_stage_times()
    if not times:
        return "Stage time data not available — requires created_at, work_start, and closed_at columns."
    lines = []
    for priority in sorted(times.keys()):
        label = f"L{priority}"
        t = times[priority]
        q = f"{t['queue_days']:.1f}d" if t.get("queue_days") is not None else "N/A"
        r = f"{t['resolution_days']:.1f}d" if t.get("resolution_days") is not None else "N/A"
        total = f"{t['total_days']:.1f}d" if t.get("total_days") is not None else "N/A"
        lines.append(f"{label} — queue: {q}, resolution: {r}, total: {total}")
    return "\n".join(lines)


@tool
def get_servicenow_ticket(number: str) -> str:
    """Get full details of a single ServiceNow ticket by its number, e.g. INC100001."""
    ticket = servicenow_store.get_ticket(number) if servicenow_store.is_loaded() else None
    if ticket is None:
        ticket = servicenow_client.get_incident(number)
    if not ticket:
        return f"Ticket {number} not found."
    return "\n".join(f"{k}: {v}" for k, v in ticket.items() if v not in (None, ""))


@tool
def get_servicenow_tickets(
    priority: int = 0,
    state: str = "",
    assignment_group: str = "",
    limit: int = 20,
) -> str:
    """
    Get a filtered list of ServiceNow tickets.
    priority: 1=L1, 2=L2, 3=L3, 4=L4, 0=all.
    state: 'open', 'in_progress', 'resolved', or '' for all.
    assignment_group: filter by team name, or '' for all.
    limit: max rows returned (default 20).
    """
    if servicenow_store.is_loaded():
        tickets = servicenow_store.get_incidents(
            state=state or None,
            priority=priority or None,
            assignment_group=assignment_group or None,
            limit=limit,
        )
    else:
        tickets = servicenow_client.get_incidents(state or None)
        if priority:
            tickets = [t for t in tickets if str(t.get("priority")) == str(priority)]
    if not tickets:
        return "No tickets found matching those filters."
    return "\n".join(
        f"{t.get('number', '?')}: [L{t.get('priority', '?')}] {t.get('short_description', '')} ({t.get('state', '')})"
        for t in tickets[:limit]
    )


@tool
def query_servicenow_sql(sql: str) -> str:
    f"""
    Run a read-only SQL SELECT query against the ServiceNow incidents database.
    Only SELECT statements are allowed.
    {_SCHEMA}
    Example: SELECT number, short_description FROM incidents WHERE priority = 1 AND state = 'open'
    """
    if not servicenow_store.is_loaded():
        return "No data loaded — upload an xlsx file first."
    try:
        rows = servicenow_store.run_sql(sql)
        if not rows:
            return "Query returned no results."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        for row in rows:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)
    except ValueError as exc:
        return f"Error: {exc}"


servicenow_tools = [
    get_servicenow_priority_summary,
    get_servicenow_stage_times,
    get_servicenow_ticket,
    get_servicenow_tickets,
    query_servicenow_sql,
]
```

- [ ] **Step 4: Update `chart_tool.py` Literal and description**

In `chatbot/tools/chart_tool.py`, replace the `RenderChartInput` class:

```python
class RenderChartInput(BaseModel):
    chart_type: Literal[
        "ticket_volume",
        "priority_donut",
        "sla_breach_line",
        "resolution_histogram",
        "cross_system_bar",
        "priority_summary_bar",
        "stage_time_bar",
    ]
    data: dict
    title: str = ""
```

And update the `render_chart` description string — replace the description parameter:

```python
render_chart = StructuredTool.from_function(
    func=_render_chart,
    name="render_chart",
    description=(
        "Render a Plotly chart in the UI. ALWAYS call this when you have data to visualize. "
        "chart_type options: "
        "ticket_volume (bar chart of issues by status — needs data.statuses dict), "
        "priority_donut (donut chart of P1-P4 counts — needs data.priorities dict), "
        "sla_breach_line (line chart over 30 days — needs data.dates list and data.breach_rates list), "
        "resolution_histogram (histogram of days to close — needs data.days_to_close list), "
        "cross_system_bar (Jira vs ServiceNow open counts — needs data.jira_open and data.servicenow_open), "
        "priority_summary_bar (grouped bar L1-L4 by state — needs data.priorities dict like {1: {'open': 3, 'resolved': 2}}), "
        "stage_time_bar (avg days per stage per priority — needs data.stage_times dict like {1: {'queue_days': 1.0, 'resolution_days': 2.0, 'total_days': 3.0}})."
    ),
    args_schema=RenderChartInput,
)
```

- [ ] **Step 5: Run all servicenow tool tests**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_servicenow_tools.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add chatbot/tools/servicenow_tools.py chatbot/tools/chart_tool.py chatbot/tests/test_servicenow_tools.py
git commit -m "feat: replace servicenow tools with 5-tool set including priority summary, stage times, and SQL fallback"
```

---

### Task 5: New chart types in `charts.py`

**Files:**
- Modify: `chatbot/visualizations/charts.py`
- Modify: `chatbot/tests/test_charts.py`

**Interfaces:**
- Consumes: nothing from other tasks
- Produces:
  - `priority_summary_bar(data, title) -> go.Figure` — `data = {"priorities": {1: {"open": 3}, ...}}`
  - `stage_time_bar(data, title) -> go.Figure` — `data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}, ...}}`
  - Both registered in `_BUILDERS` so `build_chart()` dispatches to them

- [ ] **Step 1: Write failing tests**

Add to the end of `chatbot/tests/test_charts.py`:

```python
from visualizations.charts import priority_summary_bar, stage_time_bar


def test_priority_summary_bar_returns_figure():
    data = {"priorities": {1: {"open": 3, "resolved": 1}, 2: {"in_progress": 2}}}
    fig = priority_summary_bar(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_priority_summary_bar_has_l1_to_l4_labels():
    data = {"priorities": {1: {"open": 3}, 2: {"open": 2}, 3: {"resolved": 5}, 4: {"open": 1}}}
    fig = priority_summary_bar(data)
    all_x = [x for trace in fig.data for x in (trace.x or [])]
    assert "L1" in all_x
    assert "L4" in all_x


def test_priority_summary_bar_custom_title():
    data = {"priorities": {1: {"open": 1}}}
    fig = priority_summary_bar(data, title="My Priority Chart")
    assert fig.layout.title.text == "My Priority Chart"


def test_stage_time_bar_returns_figure():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = stage_time_bar(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_stage_time_bar_has_stage_labels():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = stage_time_bar(data)
    all_x = [x for trace in fig.data for x in (trace.x or [])]
    assert any("queue" in str(x).lower() or "Queue" in str(x) for x in all_x)


def test_build_chart_dispatches_priority_summary_bar():
    data = {"priorities": {1: {"open": 2}}}
    fig = build_chart("priority_summary_bar", data)
    assert isinstance(fig, go.Figure)


def test_build_chart_dispatches_stage_time_bar():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = build_chart("stage_time_bar", data)
    assert isinstance(fig, go.Figure)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_charts.py::test_priority_summary_bar_returns_figure tests/test_charts.py::test_stage_time_bar_returns_figure -v
```

Expected: `ImportError: cannot import name 'priority_summary_bar'`

- [ ] **Step 3: Add chart builders to `charts.py`**

Add the following two functions before the `_BUILDERS` dict in `chatbot/visualizations/charts.py`:

```python
def priority_summary_bar(data: dict, title: str = "") -> go.Figure:
    priorities = data.get("priorities", {})
    all_states = sorted({s for states in priorities.values() for s in states})
    state_colors = {"open": "#EF4444", "in_progress": "#F59E0B", "resolved": "#10B981"}
    x_labels = [f"L{p}" for p in sorted(priorities.keys())]
    fig = go.Figure()
    for state in all_states:
        y_vals = [priorities.get(p, {}).get(state, 0) for p in sorted(priorities.keys())]
        fig.add_trace(go.Bar(
            name=state.replace("_", " ").title(),
            x=x_labels,
            y=y_vals,
            marker_color=state_colors.get(state, "#6B7280"),
        ))
    fig.update_layout(
        title=title or "Ticket Volume by Priority and State",
        xaxis_title="Priority",
        yaxis_title="Count",
        barmode="group",
        template="plotly_dark",
    )
    return fig


def stage_time_bar(data: dict, title: str = "") -> go.Figure:
    stage_times = data.get("stage_times", {})
    stages = ["queue_days", "resolution_days", "total_days"]
    stage_labels = ["Queue Time", "Resolution Time", "Total Time"]
    priority_colors = {"L1": "#EF4444", "L2": "#F59E0B", "L3": "#3B82F6", "L4": "#6B7280"}
    fig = go.Figure()
    for priority in sorted(stage_times.keys()):
        label = f"L{priority}"
        times = stage_times[priority]
        y_vals = [times.get(s) or 0 for s in stages]
        fig.add_trace(go.Bar(
            name=label,
            x=stage_labels,
            y=y_vals,
            marker_color=priority_colors.get(label, "#9CA3AF"),
        ))
    fig.update_layout(
        title=title or "Average Time per Stage by Priority",
        xaxis_title="Stage",
        yaxis_title="Average Days",
        barmode="group",
        template="plotly_dark",
    )
    return fig
```

Also update the `_BUILDERS` dict to include the new chart types:

```python
_BUILDERS = {
    "ticket_volume": ticket_volume_chart,
    "priority_donut": priority_donut_chart,
    "sla_breach_line": sla_breach_line_chart,
    "resolution_histogram": resolution_histogram,
    "cross_system_bar": cross_system_bar_chart,
    "priority_summary_bar": priority_summary_bar,
    "stage_time_bar": stage_time_bar,
}
```

- [ ] **Step 4: Run all chart tests**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/test_charts.py -v
```

Expected: all tests PASS (existing + 7 new).

- [ ] **Step 5: Commit**

```bash
git add chatbot/visualizations/charts.py chatbot/tests/test_charts.py
git commit -m "feat: add priority_summary_bar and stage_time_bar chart types"
```

---

### Task 6: Update `app.py` — sidebar upload UI and system prompt

**Files:**
- Modify: `chatbot/app.py`

**Interfaces:**
- Consumes: `servicenow_store.load_xlsx()`, `servicenow_store.get_last_upload()`, `servicenow_store.is_loaded()`
- Produces: updated Streamlit UI with file upload (DEV_MODE gated) and last-loaded caption

Note: `app.py` uses Streamlit which is UI-only and not unit testable. Manual verification steps are provided instead.

- [ ] **Step 1: Add store import to `app.py`**

In `chatbot/app.py`, add to the imports block:

```python
from integrations import servicenow_store
```

- [ ] **Step 2: Update the system prompt constant**

Replace `_SYSTEM_PROMPT`:

```python
_SYSTEM_PROMPT = (
    "You are a helpful IT operations assistant. You can query Jira, Slack, and ServiceNow "
    "to answer questions. ServiceNow data is loaded from an xlsx export — use "
    "get_servicenow_priority_summary for L1/L2/L3/L4 ticket counts, "
    "get_servicenow_stage_times for time spent in each stage, "
    "get_servicenow_ticket to look up a specific ticket by ID, "
    "get_servicenow_tickets to filter tickets, and "
    "query_servicenow_sql for any other ServiceNow query. "
    "When showing data with multiple items or metrics, always render a chart. "
    "Be concise and professional."
)
```

- [ ] **Step 3: Update tool list in `_build_executor`**

In `_build_executor`, update the import line to use the new 5-tool list. The existing line already imports `servicenow_tools` — no change needed there since `servicenow_tools` now exports 5 tools.

- [ ] **Step 4: Update `_render_sidebar` to add upload UI and last-loaded caption**

Replace the `_render_sidebar` function:

```python
def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Connection Status")
        status = _check_connections()
        use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

        for name in ["jira", "servicenow", "slack"]:
            dot = "🟢" if (use_mock or status.get(name)) else "🔴"
            label = "Mock" if use_mock else ("Connected" if status.get(name) else "Unreachable")
            st.write(f"{dot} **{name.capitalize()}** — {label}")

        channel_id = slack_client.get_channel_id()
        if channel_id:
            st.caption(f"Channel: {channel_id}")

        st.divider()
        st.header("ServiceNow Data")

        last = servicenow_store.get_last_upload()
        if last:
            st.caption(
                f"Loaded: **{last['filename']}** — {last['row_count']} rows — {last['uploaded_at'][:10]}"
            )
        else:
            st.caption("No data loaded.")

        if os.getenv("DEV_MODE", "false").lower() == "true":
            uploaded = st.file_uploader("Upload ServiceNow xlsx", type=["xlsx"])
            if uploaded is not None:
                with st.spinner("Loading…"):
                    try:
                        count = servicenow_store.load_xlsx(uploaded.read(), uploaded.name)
                        st.success(f"Loaded {count} rows from {uploaded.name}")
                        st.session_state["executor"] = None
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")

        st.divider()
        st.header("Settings")

        new_mock = st.toggle("Use mock data", value=use_mock)
        if new_mock != use_mock:
            os.environ["USE_MOCK_DATA"] = str(new_mock).lower()
            st.session_state["executor"] = None
            st.session_state["connection_status"] = None
            st.rerun()

        st.divider()
        st.header("Actions")

        if st.button("🔄 Refresh Slack messages"):
            st.session_state["slack_messages"] = []
            st.success("Slack cache cleared — next query will re-fetch.")

        if st.button("🗑️ Clear chat"):
            st.session_state["chat_history"] = []
            st.session_state["messages"] = []
            st.rerun()
```

- [ ] **Step 5: Run the full test suite to confirm nothing broke**

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && pytest tests/ -v
```

Expected: all tests PASS. Any failures must be fixed before proceeding.

- [ ] **Step 6: Manual smoke test**

Start the app with DEV_MODE enabled:

```bash
cd /Users/maxverhoef/ClaudeProjects/streamlit-chatbot/chatbot && DEV_MODE=true streamlit run app.py
```

Check:
1. Sidebar shows "No data loaded." caption
2. Sidebar shows a file uploader widget (DEV_MODE=true)
3. Upload the ServiceNow xlsx — should show "Loaded N rows" success message
4. Sidebar "last loaded" caption updates with filename, row count, date
5. Ask "summarise tickets by priority" — should return L1/L2/L3/L4 breakdown and render a chart
6. Ask "how long do L1 tickets take to resolve?" — should return stage time data
7. Ask "show me ticket INC100001" (or a real number from your xlsx) — should return ticket details
8. Restart the app (Ctrl+C, rerun) — "last loaded" caption should still show the previous upload (persistence check)
9. Without DEV_MODE, the file uploader should not appear

- [ ] **Step 7: Commit**

```bash
git add chatbot/app.py
git commit -m "feat: add ServiceNow xlsx upload UI and update system prompt"
```
