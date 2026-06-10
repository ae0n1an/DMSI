import os
import requests
from requests.auth import HTTPBasicAuth
from utils import mock_data


def _use_mock() -> bool:
    return os.getenv("USE_MOCK_DATA", "false").lower() == "true"


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(
        os.getenv("SERVICENOW_USERNAME", ""),
        os.getenv("SERVICENOW_PASSWORD", ""),
    )


def _base_url() -> str:
    return os.getenv("SERVICENOW_INSTANCE", "").rstrip("/")


def ping() -> bool:
    if _use_mock():
        return False
    try:
        resp = requests.get(
            f"{_base_url()}/api/now/table/incident",
            params={"sysparm_limit": 1},
            auth=_auth(),
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def get_incidents(state: str | None = None) -> list[dict]:
    if _use_mock():
        return mock_data.get_servicenow_incidents(state)
    try:
        params: dict = {
            "sysparm_limit": 100,
            "sysparm_fields": "number,short_description,state,priority,category,opened_at,resolved_at",
        }
        if state:
            state_map = {"open": "1", "in_progress": "2", "resolved": "6"}
            params["sysparm_query"] = f"state={state_map.get(state, state)}"
        resp = requests.get(
            f"{_base_url()}/api/now/table/incident",
            params=params,
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        return [_normalize(r) for r in resp.json().get("result", [])]
    except Exception:
        return mock_data.get_servicenow_incidents(state)


def get_incident(number: str) -> dict | None:
    if _use_mock():
        return mock_data.get_servicenow_incident(number)
    try:
        resp = requests.get(
            f"{_base_url()}/api/now/table/incident",
            params={"sysparm_query": f"number={number}", "sysparm_limit": 1},
            auth=_auth(),
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        return _normalize(results[0]) if results else None
    except Exception:
        return mock_data.get_servicenow_incident(number)


def get_stats() -> dict:
    if _use_mock():
        return mock_data.get_servicenow_stats()
    try:
        incidents = get_incidents()
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for inc in incidents:
            p = f"P{inc['priority']}"
            by_priority[p] = by_priority.get(p, 0) + 1
            c = inc["category"]
            by_category[c] = by_category.get(c, 0) + 1
        return {"by_priority": by_priority, "by_category": by_category}
    except Exception:
        return mock_data.get_servicenow_stats()


def _normalize(raw: dict) -> dict:
    state_map = {"1": "open", "2": "in_progress", "6": "resolved"}

    def _val(field):
        return field.get("value", "") if isinstance(field, dict) else (field or "")

    state_raw = _val(raw.get("state", ""))
    return {
        "number": raw.get("number", ""),
        "short_description": raw.get("short_description", ""),
        "state": state_map.get(str(state_raw), str(state_raw)),
        "priority": str(_val(raw.get("priority", ""))),
        "category": _val(raw.get("category", "")),
        "opened_at": raw.get("opened_at", ""),
        "resolved_at": raw.get("resolved_at", ""),
    }
