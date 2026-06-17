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
