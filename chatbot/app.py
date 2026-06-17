import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from tools.jira_tools import jira_tools
from tools.slack_tools import slack_tools
from tools.servicenow_tools import servicenow_tools
from tools.chart_tool import render_chart
from visualizations.charts import build_chart
from integrations import jira_client, slack_client, servicenow_client, servicenow_store

load_dotenv()

st.set_page_config(
    page_title="IT Ops Chatbot",
    page_icon="🤖",
    layout="wide",
)

_SYSTEM_PROMPT = (
    "You are a helpful IT operations assistant. You can query Jira, Slack, and ServiceNow "
    "to answer questions. ServiceNow data is loaded from an xlsx export — use "
    "get_servicenow_priority_summary for L1/L2/L3/L4 ticket counts, "
    "get_servicenow_stage_times for time spent in each stage, "
    "get_servicenow_ticket to look up a specific ticket by ID, "
    "get_servicenow_tickets to filter tickets, and "
    "query_servicenow_sql for any other ServiceNow query. "
    "When showing data with multiple items or metrics, always render a chart. "
    "Be concise and professional."
)


def _init_session() -> None:
    defaults = {
        "chat_history": [],
        "messages": [],
        "pending_charts": [],
        "slack_messages": [],
        "executor": None,
        "connection_status": None,
        "_last_uploaded": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _check_connections() -> dict:
    if st.session_state["connection_status"] is None:
        st.session_state["connection_status"] = {
            "jira": jira_client.ping(),
            "slack": slack_client.ping(),
            "servicenow": servicenow_client.ping(),
        }
    return st.session_state["connection_status"]


def _build_executor() -> AgentExecutor:
    if st.session_state["executor"] is not None:
        return st.session_state["executor"]

    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.2,
    )

    all_tools = [*jira_tools, *slack_tools, *servicenow_tools, render_chart]

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, all_tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=False,
        handle_parsing_errors=True,
    )
    st.session_state["executor"] = executor
    return executor


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Connection Status")
        status = _check_connections()
        use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

        for name in ["jira", "servicenow", "slack"]:
            dot = "🟢" if (use_mock or status.get(name)) else "🔴"
            label = "Mock" if use_mock else ("Connected" if status.get(name) else "Unreachable")
            st.write(f"{dot} **{name.capitalize()}** — {label}")

        channel_id = slack_client.get_channel_id()
        if channel_id:
            st.caption(f"Channel: {channel_id}")

        st.divider()
        st.header("ServiceNow Data")

        last = servicenow_store.get_last_upload()
        if last:
            st.caption(
                f"Loaded: **{last['filename']}** — {last['row_count']} rows — {last['uploaded_at'][:10]}"
            )
        else:
            st.caption("No data loaded.")

        if os.getenv("DEV_MODE", "false").lower() == "true":
            uploaded = st.file_uploader("Upload ServiceNow xlsx", type=["xlsx"])
            if uploaded is not None and st.session_state.get("_last_uploaded") != uploaded.name:
                with st.spinner("Loading…"):
                    try:
                        count = servicenow_store.load_xlsx(uploaded.read(), uploaded.name)
                        st.session_state["_last_uploaded"] = uploaded.name
                        st.session_state["executor"] = None
                        st.success(f"Loaded {count} rows from {uploaded.name}")
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")

        st.divider()
        st.header("Settings")

        new_mock = st.toggle("Use mock data", value=use_mock)
        if new_mock != use_mock:
            os.environ["USE_MOCK_DATA"] = str(new_mock).lower()
            st.session_state["executor"] = None
            st.session_state["connection_status"] = None
            st.rerun()

        st.divider()
        st.header("Actions")

        if st.button("🔄 Refresh Slack messages"):
            st.session_state["slack_messages"] = []
            st.success("Slack cache cleared — next query will re-fetch.")

        if st.button("🗑️ Clear chat"):
            st.session_state["chat_history"] = []
            st.session_state["messages"] = []
            st.rerun()


def _render_chat() -> None:
    st.title("IT Operations Chatbot")

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for chart_item in msg.get("charts", []):
                try:
                    fig = build_chart(
                        chart_item["chart_type"],
                        chart_item["data"],
                        chart_item.get("title", ""),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not render chart: {e}")

    if user_input := st.chat_input("Ask me anything about Jira, Slack, or ServiceNow…"):
        st.session_state["pending_charts"] = []
        st.session_state["messages"].append({"role": "user", "content": user_input, "charts": []})

        with st.chat_message("user"):
            st.markdown(user_input)

        executor = _build_executor()

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    result = executor.invoke({
                        "input": user_input,
                        "chat_history": st.session_state["chat_history"],
                    })
                    response = result.get("output", "Sorry, I couldn't process that request.")
                except Exception as e:
                    response = f"An error occurred: {e}"

            st.markdown(response)

            charts_to_render = list(st.session_state.get("pending_charts", []))
            st.session_state["pending_charts"] = []

            for chart_item in charts_to_render:
                try:
                    fig = build_chart(
                        chart_item["chart_type"],
                        chart_item["data"],
                        chart_item.get("title", ""),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not render chart: {e}")

        st.session_state["chat_history"].append(HumanMessage(content=user_input))
        st.session_state["chat_history"].append(AIMessage(content=response))
        st.session_state["messages"].append({
            "role": "assistant",
            "content": response,
            "charts": charts_to_render,
        })


def main() -> None:
    _init_session()
    _render_sidebar()
    _render_chat()


if __name__ == "__main__":
    main()
