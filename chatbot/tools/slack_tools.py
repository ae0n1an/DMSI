import streamlit as st
from langchain_core.tools import tool
from integrations import slack_client


@tool
def get_slack_messages(limit: int = 20) -> str:
    """Fetch recent messages from the configured Slack channel. Returns up to `limit` messages. Messages are cached in the session for faster follow-up searches."""
    if not st.session_state.get("slack_messages"):
        st.session_state["slack_messages"] = slack_client.fetch_messages(100)
    messages = st.session_state["slack_messages"][:limit]
    if not messages:
        return "No messages found in the Slack channel."
    return "\n".join(f"[{m['ts']}] {m['user']}: {m['text']}" for m in messages)


@tool
def search_slack_messages(keyword: str) -> str:
    """Search the Slack channel history for messages containing a keyword. Case-insensitive. Fetches history if not already cached."""
    if not st.session_state.get("slack_messages"):
        st.session_state["slack_messages"] = slack_client.fetch_messages(100)
    matches = slack_client.search_messages(st.session_state["slack_messages"], keyword)
    if not matches:
        return f"No messages found containing '{keyword}'."
    return "\n".join(f"[{m['ts']}] {m['user']}: {m['text']}" for m in matches)


@tool
def post_slack_message(text: str) -> str:
    """Post a message to the configured Slack channel. Returns confirmation or error."""
    result = slack_client.post_message(text)
    if result.get("ok"):
        return "Message posted successfully."
    return f"Failed to post message: {result.get('error', 'unknown error')}"


slack_tools = [get_slack_messages, search_slack_messages]
