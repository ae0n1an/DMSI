import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"

from integrations.jira_client import search_issues, get_issue, list_by_status, get_sprint_summary, ping


def test_search_issues_returns_list():
    results = search_issues("project = PROJECT-A")
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_issues_each_has_required_keys():
    results = search_issues("project = PROJECT-A")
    for issue in results:
        for key in ("key", "summary", "status", "priority"):
            assert key in issue, f"Missing key: {key}"


def test_get_issue_found():
    from utils.mock_data import JIRA_ISSUES
    key = JIRA_ISSUES[0]["key"]
    issue = get_issue(key)
    assert issue is not None
    assert issue["key"] == key


def test_get_issue_not_found():
    result = get_issue("DOESNOTEXIST-0")
    assert result is None


def test_list_by_status_filters_correctly():
    issues = list_by_status("PROJECT-A", "Open")
    assert all(i["status"] == "Open" for i in issues)
    assert all(i["key"].startswith("PROJECT-A-") for i in issues)


def test_get_sprint_summary_structure():
    summary = get_sprint_summary("1")
    assert "total" in summary
    assert "by_status" in summary
    assert isinstance(summary["total"], int)


def test_ping_mock_mode_returns_false():
    result = ping()
    assert result is False
