import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"

from tools.servicenow_tools import get_servicenow_incidents, get_servicenow_incident, get_servicenow_stats, servicenow_tools
from langchain_core.tools import BaseTool


def test_get_incidents_all():
    result = get_servicenow_incidents.invoke({"state": ""})
    assert isinstance(result, str)
    assert "INC" in result


def test_get_incidents_open_only():
    result = get_servicenow_incidents.invoke({"state": "open"})
    lines = [l for l in result.strip().split("\n") if l]
    assert all("open" in l for l in lines)


def test_get_incident_found():
    result = get_servicenow_incident.invoke({"number": "INC100001"})
    assert "INC100001" in result


def test_get_incident_not_found():
    result = get_servicenow_incident.invoke({"number": "INC999999"})
    assert "not found" in result.lower()


def test_get_stats_returns_string():
    result = get_servicenow_stats.invoke({})
    assert "by_priority" in result
    assert "by_category" in result


def test_servicenow_tools_list_has_three_tools():
    assert len(servicenow_tools) == 3
    assert all(isinstance(t, BaseTool) for t in servicenow_tools)
