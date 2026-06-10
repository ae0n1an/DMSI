import os
import requests
from requests.auth import HTTPBasicAuth
from utils import mock_data


def _use_mock() -> bool:
    return os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(os.getenv("JIRA_EMAIL", ""), os.getenv("JIRA_API_TOKEN", ""))


def _base_url() -> str:
    return os.getenv("JIRA_BASE_URL", "").rstrip("/")


def ping() -> bool:
    if _use_mock():
        return False
    try:
        resp = requests.get(f"{_base_url()}/rest/api/2/myself", auth=_auth(), timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def search_issues(jql: str) -> list[dict]:
    if _use_mock():
        return mock_data.get_jira_issues()
    try:
        resp = requests.get(
            f"{_base_url()}/rest/api/2/search",
            params={"jql": jql, "maxResults": 50},
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return [_normalize(i) for i in resp.json().get("issues", [])]
    except Exception:
        return mock_data.get_jira_issues()


def get_issue(key: str) -> dict | None:
    if _use_mock():
        return mock_data.get_jira_issue(key)
    try:
        resp = requests.get(
            f"{_base_url()}/rest/api/2/issue/{key}",
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return _normalize(resp.json())
    except Exception:
        return mock_data.get_jira_issue(key)


def list_by_status(project: str, status: str) -> list[dict]:
    if _use_mock():
        return mock_data.get_jira_issues(project=project, status=status)
    jql = f'project = "{project}" AND status = "{status}"'
    return search_issues(jql)


def get_sprint_summary(board_id: str) -> dict:
    if _use_mock():
        return _summary_from_issues(mock_data.get_jira_issues())
    try:
        resp = requests.get(
            f"{_base_url()}/rest/agile/1.0/board/{board_id}/sprint",
            params={"state": "active"},
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        sprints = resp.json().get("values", [])
        if not sprints:
            return {"total": 0, "by_status": {}, "error": "No active sprint found"}
        sprint_id = sprints[0]["id"]
        issues_resp = requests.get(
            f"{_base_url()}/rest/agile/1.0/sprint/{sprint_id}/issue",
            auth=_auth(),
            timeout=10,
        )
        issues_resp.raise_for_status()
        issues = [_normalize(i) for i in issues_resp.json().get("issues", [])]
        return _summary_from_issues(issues)
    except Exception:
        return _summary_from_issues(mock_data.get_jira_issues())


def _summary_from_issues(issues: list[dict]) -> dict:
    by_status: dict[str, int] = {}
    for issue in issues:
        s = issue["status"]
        by_status[s] = by_status.get(s, 0) + 1
    return {"total": len(issues), "by_status": by_status}


def _normalize(raw: dict) -> dict:
    fields = raw.get("fields", {})
    priority = fields.get("priority") or {}
    status = fields.get("status") or {}
    assignee = fields.get("assignee") or {}
    return {
        "key": raw.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": status.get("name", ""),
        "priority": priority.get("name", ""),
        "assignee": assignee.get("emailAddress"),
        "created": fields.get("created"),
        "resolved": fields.get("resolutiondate"),
    }
