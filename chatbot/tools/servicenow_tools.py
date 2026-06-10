from langchain_core.tools import tool
from integrations import servicenow_client


@tool
def get_servicenow_incidents(state: str = "") -> str:
    """Get ServiceNow incidents. Filter by state: 'open', 'in_progress', 'resolved', or leave empty for all incidents."""
    incidents = servicenow_client.get_incidents(state or None)
    if not incidents:
        return "No incidents found."
    return "\n".join(
        f"{i['number']}: [P{i['priority']}] {i['short_description']} ({i['state']})"
        for i in incidents
    )


@tool
def get_servicenow_incident(number: str) -> str:
    """Get full details of a single ServiceNow incident by its number, e.g. INC100001."""
    incident = servicenow_client.get_incident(number)
    if not incident:
        return f"Incident {number} not found."
    return str(incident)


@tool
def get_servicenow_stats() -> str:
    """Get summary statistics for all ServiceNow incidents: count grouped by priority (P1-P4) and by category."""
    stats = servicenow_client.get_stats()
    return str(stats)


servicenow_tools = [get_servicenow_incidents, get_servicenow_incident, get_servicenow_stats]
