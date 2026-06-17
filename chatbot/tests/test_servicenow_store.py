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
