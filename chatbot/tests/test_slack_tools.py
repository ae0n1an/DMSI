import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"
os.environ["SLACK_CHANNEL_ID"] = "C0123456789"

import streamlit as st
st.session_state.clear()

from tools.slack_tools import get_slack_messages, search_slack_messages, post_slack_message, slack_tools
from langchain_core.tools import BaseTool


def test_get_slack_messages_returns_string():
    st.session_state.clear()
    result = get_slack_messages.invoke({"limit": 5})
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_slack_messages_populates_session_state():
    st.session_state.clear()
    get_slack_messages.invoke({"limit": 10})
    assert "slack_messages" in st.session_state
    assert len(st.session_state["slack_messages"]) == 10


def test_get_slack_messages_uses_cached_session_state():
    st.session_state["slack_messages"] = [{"ts": "1", "user": "U1", "text": "cached msg", "channel_id": "C0123456789"}]
    result = get_slack_messages.invoke({"limit": 5})
    assert "cached msg" in result


def test_search_slack_messages_finds_match():
    st.session_state.clear()
    result = search_slack_messages.invoke({"keyword": "incident"})
    assert isinstance(result, str)
    assert "incident" in result.lower()


def test_search_slack_messages_no_match():
    st.session_state.clear()
    result = search_slack_messages.invoke({"keyword": "zzznomatchzzz"})
    assert "no messages found" in result.lower()


def test_post_slack_message_mock():
    result = post_slack_message.invoke({"text": "test message"})
    assert "posted successfully" in result.lower()


def test_slack_tools_list_has_three_tools():
    assert len(slack_tools) == 3
    assert all(isinstance(t, BaseTool) for t in slack_tools)
