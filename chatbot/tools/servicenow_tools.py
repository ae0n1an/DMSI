from langchain_core.tools import tool
from integrations import servicenow_client, servicenow_store

_SCHEMA = (
    "Table: incidents. Key columns: number (TEXT), short_description (TEXT), "
    "priority (INTEGER 1=L1 2=L2 3=L3 4=L4), state (TEXT e.g. open/in_progress/resolved), "
    "created_at (TEXT ISO datetime), work_start (TEXT ISO datetime), closed_at (TEXT ISO datetime), "
    "business_duration (TEXT), assignment_group (TEXT), assigned_to (TEXT), tags (TEXT), "
    "description (TEXT), due_date (TEXT), active (TEXT), raised_for (TEXT), "
    "resolution_notes (TEXT), configuration_item (TEXT), impact (TEXT), urgency (TEXT)."
)


@tool
def get_servicenow_priority_summary() -> str:
    """Get a summary of ServiceNow tickets grouped by priority level (L1/L2/L3/L4) and state."""
    summary = servicenow_store.get_priority_summary()
    if not summary:
        summary_data = servicenow_client.get_stats()
        by_p = summary_data.get("by_priority", {})
        return "\n".join(f"{k}: {v} tickets" for k, v in sorted(by_p.items())) or "No data."
    lines = []
    for priority in sorted(summary.keys()):
        label = f"L{priority}"
        states = summary[priority]
        total = sum(states.values())
        breakdown = ", ".join(f"{s}: {c}" for s, c in sorted(states.items()))
        lines.append(f"{label} — total: {total} ({breakdown})")
    return "\n".join(lines) if lines else "No data."


@tool
def get_servicenow_stage_times() -> str:
    """Get average time spent in each stage (queue time, resolution time, total time) per priority level (L1-L4)."""
    times = servicenow_store.get_stage_times()
    if not times:
        return "Stage time data not available — requires created_at, work_start, and closed_at columns."
    lines = []
    for priority in sorted(times.keys()):
        label = f"L{priority}"
        t = times[priority]
        q = f"{t['queue_days']:.1f}d" if t.get("queue_days") is not None else "N/A"
        r = f"{t['resolution_days']:.1f}d" if t.get("resolution_days") is not None else "N/A"
        total = f"{t['total_days']:.1f}d" if t.get("total_days") is not None else "N/A"
        lines.append(f"{label} — queue: {q}, resolution: {r}, total: {total}")
    return "\n".join(lines)


@tool
def get_servicenow_ticket(number: str) -> str:
    """Get full details of a single ServiceNow ticket by its number, e.g. INC100001."""
    ticket = servicenow_store.get_ticket(number) if servicenow_store.is_loaded() else None
    if ticket is None:
        ticket = servicenow_client.get_incident(number)
    if not ticket:
        return f"Ticket {number} not found."
    return "\n".join(f"{k}: {v}" for k, v in ticket.items() if v not in (None, ""))


@tool
def get_servicenow_tickets(
    priority: int = 0,
    state: str = "",
    assignment_group: str = "",
    limit: int = 20,
) -> str:
    """
    Get a filtered list of ServiceNow tickets.
    priority: 1=L1, 2=L2, 3=L3, 4=L4, 0=all.
    state: 'open', 'in_progress', 'resolved', or '' for all.
    assignment_group: filter by team name, or '' for all.
    limit: max rows returned (default 20).
    """
    if servicenow_store.is_loaded():
        tickets = servicenow_store.get_incidents(
            state=state or None,
            priority=priority or None,
            assignment_group=assignment_group or None,
            limit=limit,
        )
    else:
        tickets = servicenow_client.get_incidents(state or None)
        if priority:
            tickets = [t for t in tickets if str(t.get("priority")) == str(priority)]
    if not tickets:
        return "No tickets found matching those filters."
    return "\n".join(
        f"{t.get('number', '?')}: [L{t.get('priority', '?')}] {t.get('short_description', '')} ({t.get('state', '')})"
        for t in tickets[:limit]
    )


@tool(
    description=(
        "Run a read-only SQL SELECT query against the ServiceNow incidents database. "
        "Only SELECT statements are allowed. "
        f"{_SCHEMA} "
        "Example: SELECT number, short_description FROM incidents WHERE priority = 1 AND state = 'open'"
    )
)
def query_servicenow_sql(sql: str) -> str:
    if not servicenow_store.is_loaded():
        return "No data loaded — upload an xlsx file first."
    try:
        rows = servicenow_store.run_sql(sql)
        if not rows:
            return "Query returned no results."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        for row in rows:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)
    except ValueError as exc:
        return f"Error: {exc}"


servicenow_tools = [
    get_servicenow_priority_summary,
    get_servicenow_stage_times,
    get_servicenow_ticket,
    get_servicenow_tickets,
    query_servicenow_sql,
]
