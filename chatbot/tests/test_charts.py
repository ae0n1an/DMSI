import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
from visualizations.charts import (
    build_chart,
    ticket_volume_chart,
    priority_donut_chart,
    sla_breach_line_chart,
    resolution_histogram,
    cross_system_bar_chart,
)


def test_ticket_volume_returns_figure():
    fig = ticket_volume_chart({"statuses": {"Open": 10, "In Progress": 5, "Done": 20}})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"


def test_priority_donut_returns_figure():
    fig = priority_donut_chart({"priorities": {"P1": 3, "P2": 8, "P3": 12, "P4": 5}})
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "pie"
    assert fig.data[0].hole == 0.4


def test_sla_breach_line_returns_figure():
    dates = [f"2026-05-{i:02d}" for i in range(1, 31)]
    rates = [0.1 * (i % 5) for i in range(30)]
    fig = sla_breach_line_chart({"dates": dates, "breach_rates": rates})
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "scatter"


def test_resolution_histogram_returns_figure():
    fig = resolution_histogram({"days_to_close": [1, 2, 3, 5, 7, 10, 2, 4, 6, 8]})
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "histogram"


def test_cross_system_bar_returns_figure():
    fig = cross_system_bar_chart({"jira_open": 24, "servicenow_open": 11})
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "bar"
    assert list(fig.data[0].x) == ["Jira", "ServiceNow"]


def test_build_chart_dispatches_correctly():
    fig = build_chart("ticket_volume", {"statuses": {"Open": 5}})
    assert isinstance(fig, go.Figure)


def test_build_chart_unknown_type_raises():
    try:
        build_chart("not_a_chart", {})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_ticket_volume_custom_title():
    fig = ticket_volume_chart({"statuses": {"Open": 5}}, title="My Chart")
    assert fig.layout.title.text == "My Chart"


from visualizations.charts import priority_summary_bar, stage_time_bar


def test_priority_summary_bar_returns_figure():
    data = {"priorities": {1: {"open": 3, "resolved": 1}, 2: {"in_progress": 2}}}
    fig = priority_summary_bar(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_priority_summary_bar_has_l1_to_l4_labels():
    data = {"priorities": {1: {"open": 3}, 2: {"open": 2}, 3: {"resolved": 5}, 4: {"open": 1}}}
    fig = priority_summary_bar(data)
    all_x = [x for trace in fig.data for x in (trace.x or [])]
    assert "L1" in all_x
    assert "L4" in all_x


def test_priority_summary_bar_custom_title():
    data = {"priorities": {1: {"open": 1}}}
    fig = priority_summary_bar(data, title="My Priority Chart")
    assert fig.layout.title.text == "My Priority Chart"


def test_stage_time_bar_returns_figure():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = stage_time_bar(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_stage_time_bar_has_stage_labels():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = stage_time_bar(data)
    all_x = [x for trace in fig.data for x in (trace.x or [])]
    assert any("queue" in str(x).lower() or "Queue" in str(x) for x in all_x)


def test_build_chart_dispatches_priority_summary_bar():
    data = {"priorities": {1: {"open": 2}}}
    fig = build_chart("priority_summary_bar", data)
    assert isinstance(fig, go.Figure)


def test_build_chart_dispatches_stage_time_bar():
    data = {"stage_times": {1: {"queue_days": 1.0, "resolution_days": 2.0, "total_days": 3.0}}}
    fig = build_chart("stage_time_bar", data)
    assert isinstance(fig, go.Figure)
