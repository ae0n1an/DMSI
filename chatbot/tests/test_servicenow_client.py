import sys, os
import unittest.mock as mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"

from integrations import servicenow_client
from integrations.servicenow_client import get_incidents, get_incident, get_stats, ping


def test_get_incidents_all():
    incidents = get_incidents()
    assert isinstance(incidents, list)
    assert len(incidents) == 20


def test_get_incidents_filter_open():
    incidents = get_incidents("open")
    assert all(i["state"] == "open" for i in incidents)
    assert len(incidents) > 0


def test_get_incidents_filter_in_progress():
    incidents = get_incidents("in_progress")
    assert all(i["state"] == "in_progress" for i in incidents)


def test_get_incidents_filter_resolved():
    incidents = get_incidents("resolved")
    assert all(i["state"] == "resolved" for i in incidents)


def test_get_incident_found():
    result = get_incident("INC100001")
    assert result is not None
    assert result["number"] == "INC100001"


def test_get_incident_not_found():
    result = get_incident("INC999999")
    assert result is None


def test_get_stats_structure():
    stats = get_stats()
    assert "by_priority" in stats
    assert "by_category" in stats


def test_get_stats_counts_sum_to_total():
    stats = get_stats()
    assert sum(stats["by_priority"].values()) == 20
    assert sum(stats["by_category"].values()) == 20


def test_ping_mock_mode_returns_false():
    assert ping() is False


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
