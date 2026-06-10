import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["USE_MOCK_DATA"] = "true"
os.environ["SLACK_CHANNEL_ID"] = "C0123456789"

from integrations.slack_client import fetch_messages, post_message, search_messages, get_channel_id, ping


def test_fetch_messages_returns_list():
    messages = fetch_messages()
    assert isinstance(messages, list)
    assert len(messages) == 10


def test_fetch_messages_have_required_keys():
    messages = fetch_messages()
    for msg in messages:
        for key in ("ts", "user", "text", "channel_id"):
            assert key in msg, f"Missing key: {key}"


def test_search_messages_finds_keyword():
    messages = fetch_messages()
    results = search_messages(messages, "incident")
    assert len(results) > 0
    assert all("incident" in m["text"].lower() for m in results)


def test_search_messages_no_match():
    messages = fetch_messages()
    results = search_messages(messages, "zzznomatchzzz")
    assert results == []


def test_search_messages_case_insensitive():
    messages = fetch_messages()
    lower = search_messages(messages, "p1")
    upper = search_messages(messages, "P1")
    assert len(lower) == len(upper)


def test_post_message_mock_returns_ok():
    result = post_message("Hello from tests")
    assert result["ok"] is True
    assert result.get("mock") is True


def test_get_channel_id_returns_env_value():
    assert get_channel_id() == "C0123456789"


def test_ping_mock_mode_returns_false():
    assert ping() is False
