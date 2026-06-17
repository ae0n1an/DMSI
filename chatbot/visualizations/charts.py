import statistics
import plotly.graph_objects as go


def ticket_volume_chart(data: dict, title: str = "") -> go.Figure:
    statuses = data.get("statuses", {})
    colors = {"Open": "#EF4444", "In Progress": "#F59E0B", "Done": "#10B981"}
    marker_colors = [colors.get(s, "#6B7280") for s in statuses.keys()]
    fig = go.Figure(go.Bar(
        x=list(statuses.keys()),
        y=list(statuses.values()),
        marker_color=marker_colors,
    ))
    fig.update_layout(
        title=title or "Ticket Volume by Status",
        xaxis_title="Status",
        yaxis_title="Count",
        template="plotly_dark",
    )
    return fig


def priority_donut_chart(data: dict, title: str = "") -> go.Figure:
    priorities = data.get("priorities", {})
    fig = go.Figure(go.Pie(
        labels=list(priorities.keys()),
        values=list(priorities.values()),
        hole=0.4,
        marker_colors=["#EF4444", "#F59E0B", "#3B82F6", "#6B7280"],
    ))
    fig.update_layout(
        title=title or "Ticket Priority Breakdown",
        template="plotly_dark",
    )
    return fig


def sla_breach_line_chart(data: dict, title: str = "") -> go.Figure:
    dates = data.get("dates", [])
    rates = data.get("breach_rates", [])
    fig = go.Figure(go.Scatter(
        x=dates,
        y=rates,
        mode="lines+markers",
        line=dict(color="#EF4444"),
    ))
    fig.update_layout(
        title=title or "SLA Breach Rate (Last 30 Days)",
        xaxis_title="Date",
        yaxis_title="Breach Rate",
        yaxis_tickformat=".0%",
        template="plotly_dark",
    )
    return fig


def resolution_histogram(data: dict, title: str = "") -> go.Figure:
    days = data.get("days_to_close", [])
    median_val = statistics.median(days) if days else 0
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=days, nbinsx=20, marker_color="#3B82F6"))
    fig.add_vline(
        x=median_val,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Median: {median_val:.1f}d",
    )
    fig.update_layout(
        title=title or "Resolution Time Distribution",
        xaxis_title="Days to Close",
        yaxis_title="Count",
        template="plotly_dark",
    )
    return fig


def cross_system_bar_chart(data: dict, title: str = "") -> go.Figure:
    fig = go.Figure(go.Bar(
        x=["Jira", "ServiceNow"],
        y=[data.get("jira_open", 0), data.get("servicenow_open", 0)],
        marker_color=["#3B82F6", "#10B981"],
    ))
    fig.update_layout(
        title=title or "Open Tickets: Jira vs ServiceNow",
        xaxis_title="System",
        yaxis_title="Open Tickets",
        template="plotly_dark",
    )
    return fig


def priority_summary_bar(data: dict, title: str = "") -> go.Figure:
    priorities = data.get("priorities", {})
    all_states = sorted({s for states in priorities.values() for s in states})
    state_colors = {"open": "#EF4444", "in_progress": "#F59E0B", "resolved": "#10B981"}
    x_labels = [f"L{p}" for p in sorted(priorities.keys())]
    fig = go.Figure()
    for state in all_states:
        y_vals = [priorities.get(p, {}).get(state, 0) for p in sorted(priorities.keys())]
        fig.add_trace(go.Bar(
            name=state.replace("_", " ").title(),
            x=x_labels,
            y=y_vals,
            marker_color=state_colors.get(state, "#6B7280"),
        ))
    fig.update_layout(
        title=title or "Ticket Volume by Priority and State",
        xaxis_title="Priority",
        yaxis_title="Count",
        barmode="group",
        template="plotly_dark",
    )
    return fig


def stage_time_bar(data: dict, title: str = "") -> go.Figure:
    stage_times = data.get("stage_times", {})
    stages = ["queue_days", "resolution_days", "total_days"]
    stage_labels = ["Queue Time", "Resolution Time", "Total Time"]
    priority_colors = {"L1": "#EF4444", "L2": "#F59E0B", "L3": "#3B82F6", "L4": "#6B7280"}
    fig = go.Figure()
    for priority in sorted(stage_times.keys()):
        label = f"L{priority}"
        times = stage_times[priority]
        y_vals = [times.get(s) or 0 for s in stages]
        fig.add_trace(go.Bar(
            name=label,
            x=stage_labels,
            y=y_vals,
            marker_color=priority_colors.get(label, "#9CA3AF"),
        ))
    fig.update_layout(
        title=title or "Average Time per Stage by Priority",
        xaxis_title="Stage",
        yaxis_title="Average Days",
        barmode="group",
        template="plotly_dark",
    )
    return fig


_BUILDERS = {
    "ticket_volume": ticket_volume_chart,
    "priority_donut": priority_donut_chart,
    "sla_breach_line": sla_breach_line_chart,
    "resolution_histogram": resolution_histogram,
    "cross_system_bar": cross_system_bar_chart,
    "priority_summary_bar": priority_summary_bar,
    "stage_time_bar": stage_time_bar,
}


def build_chart(chart_type: str, data: dict, title: str = "") -> go.Figure:
    builder = _BUILDERS.get(chart_type)
    if not builder:
        raise ValueError(f"Unknown chart type: {chart_type!r}. Valid: {list(_BUILDERS)}")
    return builder(data, title)
