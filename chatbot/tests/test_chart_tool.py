import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
st.session_state.clear()

from tools.chart_tool import render_chart
from langchain_core.tools import BaseTool


def test_render_chart_is_a_tool():
    assert isinstance(render_chart, BaseTool)


def test_render_chart_writes_to_pending_charts():
    st.session_state.clear()
    render_chart.invoke({
        "chart_type": "ticket_volume",
        "data": {"statuses": {"Open": 5, "Done": 10}},
        "title": "",
    })
    assert "pending_charts" in st.session_state
    assert len(st.session_state["pending_charts"]) == 1
    assert st.session_state["pending_charts"][0]["chart_type"] == "ticket_volume"


def test_render_chart_appends_multiple():
    st.session_state.clear()
    render_chart.invoke({"chart_type": "ticket_volume", "data": {"statuses": {}}, "title": ""})
    render_chart.invoke({"chart_type": "priority_donut", "data": {"priorities": {}}, "title": ""})
    assert len(st.session_state["pending_charts"]) == 2


def test_render_chart_stores_data_and_title():
    st.session_state.clear()
    data = {"jira_open": 10, "servicenow_open": 5}
    render_chart.invoke({"chart_type": "cross_system_bar", "data": data, "title": "My Title"})
    entry = st.session_state["pending_charts"][0]
    assert entry["data"] == data
    assert entry["title"] == "My Title"


def test_render_chart_returns_confirmation_string():
    st.session_state.clear()
    result = render_chart.invoke({"chart_type": "priority_donut", "data": {}, "title": ""})
    assert isinstance(result, str)
    assert "priority_donut" in result
