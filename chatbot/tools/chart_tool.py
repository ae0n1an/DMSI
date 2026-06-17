from typing import Literal
from pydantic import BaseModel
import streamlit as st
from langchain_core.tools import StructuredTool


class RenderChartInput(BaseModel):
    chart_type: Literal[
        "ticket_volume",
        "priority_donut",
        "sla_breach_line",
        "resolution_histogram",
        "cross_system_bar",
        "priority_summary_bar",
        "stage_time_bar",
    ]
    data: dict
    title: str = ""


def _render_chart(chart_type: str, data: dict, title: str = "") -> str:
    if "pending_charts" not in st.session_state:
        st.session_state["pending_charts"] = []
    st.session_state["pending_charts"].append({
        "chart_type": chart_type,
        "data": data,
        "title": title,
    })
    return f"Chart '{chart_type}' queued for rendering."


render_chart = StructuredTool.from_function(
    func=_render_chart,
    name="render_chart",
    description=(
        "Render a Plotly chart in the UI. ALWAYS call this when you have data to visualize. "
        "chart_type options: "
        "ticket_volume (bar chart of issues by status — needs data.statuses dict), "
        "priority_donut (donut chart of P1-P4 counts — needs data.priorities dict), "
        "sla_breach_line (line chart over 30 days — needs data.dates list and data.breach_rates list), "
        "resolution_histogram (histogram of days to close — needs data.days_to_close list), "
        "cross_system_bar (Jira vs ServiceNow open counts — needs data.jira_open and data.servicenow_open), "
        "priority_summary_bar (grouped bar L1-L4 by state — needs data.priorities dict like {1: {'open': 3, 'resolved': 2}}), "
        "stage_time_bar (avg days per stage per priority — needs data.stage_times dict like {1: {'queue_days': 1.0, 'resolution_days': 2.0, 'total_days': 3.0}})."
    ),
    args_schema=RenderChartInput,
)
