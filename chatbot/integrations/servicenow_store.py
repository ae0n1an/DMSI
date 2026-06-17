import io
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servicenow.db")

_COLUMN_MAP = {
    "number": "number",
    "short description": "short_description",
    "priority": "priority",
    "state": "state",
    "created": "created_at",
    "work start": "work_start",
    "closed": "closed_at",
    "business duration": "business_duration",
    "assignment group": "assignment_group",
    "assigned to": "assigned_to",
    "tags": "tags",
    "description": "description",
    "due date": "due_date",
    "active": "active",
    "raised for": "raised_for",
    "resolution notes": "resolution_notes",
    "configuration item": "configuration_item",
    "impact": "impact",
    "urgency": "urgency",
}


def _normalize_col(header: str) -> str:
    lower = header.lower().strip()
    return _COLUMN_MAP.get(lower, re.sub(r"\s+", "_", lower))


def _normalize_priority(val) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    m = re.match(r"^(\d+)", str(val).strip())
    return int(m.group(1)) if m else None


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_upload_log(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            row_count INTEGER,
            uploaded_at TEXT
        )
        """
    )
    conn.commit()


def is_loaded() -> bool:
    try:
        with _conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM incidents")
            return cur.fetchone()[0] > 0
    except Exception:
        return False


def load_xlsx(file_bytes: bytes, filename: str) -> int:
    df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    df.columns = [_normalize_col(c) for c in df.columns]
    if "priority" in df.columns:
        df["priority"] = df["priority"].apply(_normalize_priority)
    row_count = len(df)
    with _conn() as conn:
        _ensure_upload_log(conn)
        df.to_sql("incidents", conn, if_exists="replace", index=False)
        conn.execute(
            "INSERT INTO upload_log (filename, row_count, uploaded_at) VALUES (?, ?, ?)",
            (filename, row_count, datetime.utcnow().isoformat()),
        )
        conn.commit()
    return row_count


def get_last_upload() -> dict | None:
    try:
        with _conn() as conn:
            _ensure_upload_log(conn)
            cur = conn.execute(
                "SELECT filename, row_count, uploaded_at FROM upload_log ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def get_incidents(
    state: str | None = None,
    priority: int | None = None,
    assignment_group: str | None = None,
    limit: int = 100,
) -> list[dict]:
    conditions, params = [], []
    if state:
        conditions.append("state = ?")
        params.append(state)
    if priority is not None:
        conditions.append("priority = ?")
        params.append(priority)
    if assignment_group:
        conditions.append("assignment_group = ?")
        params.append(assignment_group)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    try:
        with _conn() as conn:
            cur = conn.execute(f"SELECT * FROM incidents {where} LIMIT ?", params)
            return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def get_priority_summary() -> dict:
    try:
        with _conn() as conn:
            cur = conn.execute(
                "SELECT priority, state, COUNT(*) as cnt FROM incidents GROUP BY priority, state"
            )
            result: dict = {}
            for row in cur.fetchall():
                p = row["priority"]
                s = str(row["state"]).lower() if row["state"] else "unknown"
                if p not in result:
                    result[p] = {}
                result[p][s] = row["cnt"]
            return result
    except Exception:
        return {}


def get_stage_times() -> dict:
    try:
        with _conn() as conn:
            df = pd.read_sql(
                "SELECT priority, created_at, work_start, closed_at FROM incidents", conn
            )
        for col in ("created_at", "work_start", "closed_at"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df["queue_days"] = (df["work_start"] - df["created_at"]).dt.total_seconds() / 86400
        df["resolution_days"] = (df["closed_at"] - df["work_start"]).dt.total_seconds() / 86400
        df["total_days"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 86400
        result = {}
        for priority, grp in df.groupby("priority"):
            result[int(priority)] = {
                "queue_days": _safe_mean(grp["queue_days"]),
                "resolution_days": _safe_mean(grp["resolution_days"]),
                "total_days": _safe_mean(grp["total_days"]),
            }
        return result
    except Exception:
        return {}


def _safe_mean(series: "pd.Series") -> float | None:
    valid = series.dropna()
    return round(float(valid.mean()), 2) if not valid.empty else None


def get_ticket(number: str) -> dict | None:
    try:
        with _conn() as conn:
            cur = conn.execute(
                "SELECT * FROM incidents WHERE number = ? LIMIT 1", (number,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def run_sql(sql: str) -> list[dict]:
    stripped = sql.strip().lstrip(";").strip().upper()
    if not stripped.startswith("SELECT"):
        raise ValueError("Only SELECT statements are permitted.")
    try:
        with _conn() as conn:
            cur = conn.execute(sql)
            return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error as exc:
        raise ValueError(f"SQL error: {exc}") from exc
