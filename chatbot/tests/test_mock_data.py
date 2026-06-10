import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.mock_data import (
    get_jira_issues, get_jira_issue,
    get_servicenow_incidents, get_servicenow_incident, get_servicenow_stats,
    get_slack_messages,
    JIRA_ISSUES, SERVICENOW_INCIDENTS, SLACK_MESSAGES,
)


def test_jira_total_count():
    assert len(JIRA_ISSUES) == 50


def test_jira_filter_status():
    issues = get_jira_issues(status="Open")
    assert all(i["status"] == "Open" for i in issues)
    assert len(issues) > 0


def test_jira_filter_priority():
    issues = get_jira_issues(priority="P1")
    assert all(i["priority"] == "P1" for i in issues)


def test_jira_issue_has_required_keys():
    issue = JIRA_ISSUES[0]
    for key in ("key", "summary", "status", "priority", "assignee", "created"):
        assert key in issue, f"Missing key: {key}"


def test_get_jira_issue_by_key():
    key = JIRA_ISSUES[5]["key"]
    result = get_jira_issue(key)
    assert result is not None
    assert result["key"] == key


def test_get_jira_issue_missing():
    assert get_jira_issue("NOTEXIST-999") is None


def test_servicenow_total_count():
    assert len(SERVICENOW_INCIDENTS) == 20


def test_servicenow_filter_state():
    incidents = get_servicenow_incidents(state="open")
    assert all(i["state"] == "open" for i in incidents)


def test_servicenow_incident_has_required_keys():
    inc = SERVICENOW_INCIDENTS[0]
    for key in ("number", "short_description", "state", "priority", "category"):
        assert key in inc, f"Missing key: {key}"


def test_get_servicenow_incident_by_number():
    number = SERVICENOW_INCIDENTS[0]["number"]
    result = get_servicenow_incident(number)
    assert result is not None
    assert result["number"] == number


def test_servicenow_stats_structure():
    stats = get_servicenow_stats()
    assert "by_priority" in stats
    assert "by_category" in stats
    assert sum(stats["by_priority"].values()) == 20


def test_slack_total_count():
    assert len(SLACK_MESSAGES) == 10


def test_slack_messages_have_channel_id():
    for msg in SLACK_MESSAGES:
        assert "channel_id" in msg
        assert msg["channel_id"].startswith("C")
