import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils import mock_data

log = logging.getLogger(__name__)


def _use_mock() -> bool:
    return os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def _channel_id() -> str:
    return os.getenv("SLACK_CHANNEL_ID", "")


def _client() -> WebClient:
    return WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))


def ping() -> bool:
    if _use_mock():
        return False
    try:
        _client().auth_test()
        return True
    except Exception as exc:
        log.warning("Slack ping error: %s", exc)
        return False


def fetch_messages(limit: int = 100) -> list[dict]:
    if _use_mock():
        return mock_data.get_slack_messages()
    try:
        resp = _client().conversations_history(channel=_channel_id(), limit=limit)
        return [
            {
                "ts": m["ts"],
                "user": m.get("user", ""),
                "text": m.get("text", ""),
                "channel_id": _channel_id(),
            }
            for m in resp.get("messages", [])
        ]
    except Exception:
        return mock_data.get_slack_messages()


def post_message(text: str) -> dict:
    if _use_mock():
        return {"ok": True, "mock": True, "text": text}
    try:
        resp = _client().chat_postMessage(channel=_channel_id(), text=text)
        return {"ok": True, "ts": resp["ts"]}
    except SlackApiError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def search_messages(messages: list[dict], keyword: str) -> list[dict]:
    kw = keyword.lower()
    return [m for m in messages if kw in m.get("text", "").lower()]


def get_channel_id() -> str:
    return _channel_id()
