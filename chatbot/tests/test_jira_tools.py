import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"

from tools.jira_tools import search_jira_issues, get_jira_issue, list_jira_issues_by_status, get_jira_sprint_summary, jira_tools
from langchain_core.tools import BaseTool


def test_search_jira_issues_returns_string():
    result = search_jira_issues.invoke({"jql": "project = PROJECT-A"})
    assert isinstance(result, str)
    assert "PROJECT-A" in result


def test_search_jira_issues_format():
    result = search_jira_issues.invoke({"jql": "project = PROJECT-A"})
    lines = result.strip().split("\n")
    assert len(lines) > 0
    assert ":" in lines[0]


def test_get_jira_issue_found():
    from utils.mock_data import JIRA_ISSUES
    key = JIRA_ISSUES[0]["key"]
    result = get_jira_issue.invoke({"key": key})
    assert key in result


def test_get_jira_issue_not_found():
    result = get_jira_issue.invoke({"key": "NOTEXIST-0"})
    assert "not found" in result.lower()


def test_list_jira_issues_by_status():
    result = list_jira_issues_by_status.invoke({"project": "PROJECT-A", "status": "Open"})
    assert isinstance(result, str)
    assert "PROJECT-A" in result


def test_get_jira_sprint_summary():
    result = get_jira_sprint_summary.invoke({"board_id": "1"})
    assert "total" in result


def test_jira_tools_list_has_four_tools():
    assert len(jira_tools) == 4
    assert all(isinstance(t, BaseTool) for t in jira_tools)
