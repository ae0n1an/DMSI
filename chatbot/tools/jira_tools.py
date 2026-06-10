from langchain_core.tools import tool
from integrations import jira_client


@tool
def search_jira_issues(jql: str) -> str:
    """Search Jira issues using a JQL query string. Returns matching issues with key, priority, summary, and status. Example JQL: 'project = PROJECT-A AND priority = P1'"""
    issues = jira_client.search_issues(jql)
    if not issues:
        return "No issues found."
    return "\n".join(
        f"{i['key']}: [{i['priority']}] {i['summary']} ({i['status']})" for i in issues
    )


@tool
def get_jira_issue(key: str) -> str:
    """Get full details of a single Jira issue by its key, e.g. PROJECT-A-1."""
    issue = jira_client.get_issue(key)
    if not issue:
        return f"Issue {key} not found."
    return str(issue)


@tool
def list_jira_issues_by_status(project: str, status: str) -> str:
    """List Jira issues in a project filtered by status. project is the project key (e.g. PROJECT-A). status is one of: Open, In Progress, Done."""
    issues = jira_client.list_by_status(project, status)
    if not issues:
        return f"No '{status}' issues found in {project}."
    return "\n".join(f"{i['key']}: [{i['priority']}] {i['summary']}" for i in issues)


@tool
def get_jira_sprint_summary(board_id: str) -> str:
    """Get a summary of the active sprint for a Jira board. Returns total issues and breakdown by status."""
    summary = jira_client.get_sprint_summary(board_id)
    return str(summary)


jira_tools = [search_jira_issues, get_jira_issue, list_jira_issues_by_status, get_jira_sprint_summary]
