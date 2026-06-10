from datetime import datetime, timedelta

def _date(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


JIRA_ISSUES = [
    {"key": "PROJECT-A-1",  "summary": "Fix login bug causing session timeout",        "status": "Open",        "priority": "P1", "assignee": "alice@example.com", "created": _date(30), "resolved": None},
    {"key": "PROJECT-A-2",  "summary": "Deploy new auth service to staging",            "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(25), "resolved": None},
    {"key": "PROJECT-A-3",  "summary": "Update TLS certificates before expiry",         "status": "Done",        "priority": "P1", "assignee": "carol@example.com", "created": _date(40), "resolved": _date(5)},
    {"key": "PROJECT-A-4",  "summary": "Investigate memory leak in worker service",     "status": "Open",        "priority": "P2", "assignee": "alice@example.com", "created": _date(10), "resolved": None},
    {"key": "PROJECT-A-5",  "summary": "Patch CVE-2024-1234 on all prod servers",       "status": "In Progress", "priority": "P1", "assignee": "bob@example.com",   "created": _date(7),  "resolved": None},
    {"key": "PROJECT-A-6",  "summary": "Rotate API keys for third-party integrations",  "status": "Done",        "priority": "P3", "assignee": "carol@example.com", "created": _date(50), "resolved": _date(20)},
    {"key": "PROJECT-A-7",  "summary": "Set up alerting for disk usage thresholds",     "status": "Open",        "priority": "P3", "assignee": None,               "created": _date(15), "resolved": None},
    {"key": "PROJECT-A-8",  "summary": "Archive old log files to cold storage",         "status": "Done",        "priority": "P4", "assignee": "alice@example.com", "created": _date(60), "resolved": _date(30)},
    {"key": "PROJECT-A-9",  "summary": "Add rate limiting to public API endpoints",     "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(12), "resolved": None},
    {"key": "PROJECT-A-10", "summary": "Document disaster recovery runbook",            "status": "Open",        "priority": "P4", "assignee": None,               "created": _date(20), "resolved": None},
    {"key": "PROJECT-A-11", "summary": "Fix race condition in job scheduler",           "status": "Open",        "priority": "P1", "assignee": "carol@example.com", "created": _date(3),  "resolved": None},
    {"key": "PROJECT-A-12", "summary": "Upgrade Postgres to 15.x",                     "status": "Done",        "priority": "P2", "assignee": "alice@example.com", "created": _date(45), "resolved": _date(10)},
    {"key": "PROJECT-A-13", "summary": "Add distributed tracing to microservices",      "status": "In Progress", "priority": "P3", "assignee": "bob@example.com",   "created": _date(18), "resolved": None},
    {"key": "PROJECT-A-14", "summary": "Resolve EU region latency spike",               "status": "Open",        "priority": "P1", "assignee": "carol@example.com", "created": _date(2),  "resolved": None},
    {"key": "PROJECT-A-15", "summary": "Clean up unused IAM roles",                    "status": "Done",        "priority": "P4", "assignee": "alice@example.com", "created": _date(55), "resolved": _date(25)},
    {"key": "PROJECT-A-16", "summary": "Configure WAF rules for OWASP top 10",         "status": "Open",        "priority": "P2", "assignee": None,               "created": _date(8),  "resolved": None},
    {"key": "PROJECT-A-17", "summary": "Migrate secrets to Vault",                     "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(22), "resolved": None},

    {"key": "PROJECT-B-1",  "summary": "Restore nightly backup automation",             "status": "Open",        "priority": "P1", "assignee": "alice@example.com", "created": _date(5),  "resolved": None},
    {"key": "PROJECT-B-2",  "summary": "Fix Slack webhook integration",                 "status": "Done",        "priority": "P3", "assignee": "carol@example.com", "created": _date(35), "resolved": _date(15)},
    {"key": "PROJECT-B-3",  "summary": "Add health check endpoint to all services",     "status": "In Progress", "priority": "P3", "assignee": "bob@example.com",   "created": _date(14), "resolved": None},
    {"key": "PROJECT-B-4",  "summary": "Decommission legacy SOAP service",              "status": "Done",        "priority": "P4", "assignee": "alice@example.com", "created": _date(70), "resolved": _date(35)},
    {"key": "PROJECT-B-5",  "summary": "P1 - Payment service returning 500 errors",     "status": "Open",        "priority": "P1", "assignee": "carol@example.com", "created": _date(1),  "resolved": None},
    {"key": "PROJECT-B-6",  "summary": "Enable MFA for all admin accounts",             "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(9),  "resolved": None},
    {"key": "PROJECT-B-7",  "summary": "Audit and tighten S3 bucket policies",          "status": "Open",        "priority": "P2", "assignee": None,               "created": _date(11), "resolved": None},
    {"key": "PROJECT-B-8",  "summary": "Set up canary deployment pipeline",             "status": "Done",        "priority": "P3", "assignee": "alice@example.com", "created": _date(42), "resolved": _date(18)},
    {"key": "PROJECT-B-9",  "summary": "Fix intermittent Redis cache miss",             "status": "Open",        "priority": "P3", "assignee": "carol@example.com", "created": _date(16), "resolved": None},
    {"key": "PROJECT-B-10", "summary": "Add SLA monitoring dashboard",                  "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(6),  "resolved": None},
    {"key": "PROJECT-B-11", "summary": "Resolve DNS resolution failures in k8s",        "status": "Open",        "priority": "P1", "assignee": "alice@example.com", "created": _date(4),  "resolved": None},
    {"key": "PROJECT-B-12", "summary": "Tune autoscaling thresholds for peak load",    "status": "Done",        "priority": "P3", "assignee": "carol@example.com", "created": _date(28), "resolved": _date(8)},
    {"key": "PROJECT-B-13", "summary": "Write runbook for on-call incident response",   "status": "Open",        "priority": "P4", "assignee": None,               "created": _date(19), "resolved": None},
    {"key": "PROJECT-B-14", "summary": "Block traffic from flagged IP ranges",          "status": "In Progress", "priority": "P2", "assignee": "bob@example.com",   "created": _date(13), "resolved": None},
    {"key": "PROJECT-B-15", "summary": "Upgrade Node.js runtime to LTS 20",            "status": "Done",        "priority": "P4", "assignee": "alice@example.com", "created": _date(38), "resolved": _date(12)},
    {"key": "PROJECT-B-16", "summary": "Investigate high GC pressure in JVM service",   "status": "Open",        "priority": "P2", "assignee": "carol@example.com", "created": _date(6),  "resolved": None},

    {"key": "PROJECT-C-1",  "summary": "Set up CDN caching for static assets",          "status": "Done",        "priority": "P3", "assignee": "bob@example.com",   "created": _date(48), "resolved": _date(22)},
    {"key": "PROJECT-C-2",  "summary": "Critical: API gateway returning 502s",          "status": "Open",        "priority": "P1", "assignee": "alice@example.com", "created": _date(1),  "resolved": None},
    {"key": "PROJECT-C-3",  "summary": "Implement circuit breaker for downstream deps", "status": "In Progress", "priority": "P2", "assignee": "carol@example.com", "created": _date(17), "resolved": None},
    {"key": "PROJECT-C-4",  "summary": "Enforce HTTPS everywhere",                      "status": "Done",        "priority": "P2", "assignee": "bob@example.com",   "created": _date(52), "resolved": _date(27)},
    {"key": "PROJECT-C-5",  "summary": "Fix broken CI pipeline on main branch",         "status": "Open",        "priority": "P2", "assignee": "alice@example.com", "created": _date(3),  "resolved": None},
    {"key": "PROJECT-C-6",  "summary": "Add retry logic to message queue consumers",    "status": "In Progress", "priority": "P3", "assignee": "carol@example.com", "created": _date(21), "resolved": None},
    {"key": "PROJECT-C-7",  "summary": "Review and fix CORS policy",                    "status": "Done",        "priority": "P3", "assignee": "bob@example.com",   "created": _date(33), "resolved": _date(9)},
    {"key": "PROJECT-C-8",  "summary": "Enable audit logging for all DB writes",        "status": "Open",        "priority": "P2", "assignee": None,               "created": _date(10), "resolved": None},
    {"key": "PROJECT-C-9",  "summary": "P1 - Search service returning stale results",   "status": "Open",        "priority": "P1", "assignee": "alice@example.com", "created": _date(2),  "resolved": None},
    {"key": "PROJECT-C-10", "summary": "Automate SSL cert renewal with Let's Encrypt",  "status": "Done",        "priority": "P3", "assignee": "carol@example.com", "created": _date(44), "resolved": _date(16)},
    {"key": "PROJECT-C-11", "summary": "Reduce cold start time in Lambda functions",    "status": "In Progress", "priority": "P3", "assignee": "bob@example.com",   "created": _date(15), "resolved": None},
    {"key": "PROJECT-C-12", "summary": "Fix cross-region replication lag",              "status": "Open",        "priority": "P2", "assignee": "alice@example.com", "created": _date(7),  "resolved": None},
    {"key": "PROJECT-C-13", "summary": "Write integration tests for billing service",   "status": "Done",        "priority": "P4", "assignee": "carol@example.com", "created": _date(36), "resolved": _date(14)},
    {"key": "PROJECT-C-14", "summary": "Investigate high p99 latency on checkout API", "status": "Open",        "priority": "P1", "assignee": "bob@example.com",   "created": _date(4),  "resolved": None},
    {"key": "PROJECT-C-15", "summary": "Add structured logging to all services",        "status": "In Progress", "priority": "P4", "assignee": "alice@example.com", "created": _date(23), "resolved": None},
    {"key": "PROJECT-C-16", "summary": "Update dependency versions to fix CVEs",        "status": "Done",        "priority": "P2", "assignee": "carol@example.com", "created": _date(29), "resolved": _date(6)},
    {"key": "PROJECT-C-17", "summary": "Investigate flaky E2E tests in CI",             "status": "Open",        "priority": "P3", "assignee": None,               "created": _date(11), "resolved": None},
]

SERVICENOW_INCIDENTS = [
    {"number": "INC100001", "short_description": "Network switch unresponsive in rack B",       "state": "open",        "priority": "1", "category": "network",   "opened_at": _date(8),  "resolved_at": None},
    {"number": "INC100002", "short_description": "User unable to login after password reset",   "state": "resolved",    "priority": "3", "category": "access",    "opened_at": _date(15), "resolved_at": _date(13)},
    {"number": "INC100003", "short_description": "High CPU on prod-db-01",                      "state": "in_progress", "priority": "2", "category": "hardware",  "opened_at": _date(3),  "resolved_at": None},
    {"number": "INC100004", "short_description": "Email service returning 503",                 "state": "open",        "priority": "2", "category": "software",  "opened_at": _date(1),  "resolved_at": None},
    {"number": "INC100005", "short_description": "SLA breach on INC100001",                     "state": "open",        "priority": "1", "category": "network",   "opened_at": _date(5),  "resolved_at": None},
    {"number": "INC100006", "short_description": "Disk full on backup server",                  "state": "resolved",    "priority": "2", "category": "hardware",  "opened_at": _date(20), "resolved_at": _date(18)},
    {"number": "INC100007", "short_description": "VPN connectivity issues for remote users",    "state": "in_progress", "priority": "2", "category": "network",   "opened_at": _date(4),  "resolved_at": None},
    {"number": "INC100008", "short_description": "Application deployment failed on prod",       "state": "open",        "priority": "1", "category": "software",  "opened_at": _date(2),  "resolved_at": None},
    {"number": "INC100009", "short_description": "Printer not working in meeting room 4",       "state": "resolved",    "priority": "4", "category": "hardware",  "opened_at": _date(12), "resolved_at": _date(10)},
    {"number": "INC100010", "short_description": "Database connection pool exhausted",          "state": "open",        "priority": "1", "category": "software",  "opened_at": _date(1),  "resolved_at": None},
    {"number": "INC100011", "short_description": "LDAP sync failing for new user accounts",     "state": "in_progress", "priority": "3", "category": "access",    "opened_at": _date(6),  "resolved_at": None},
    {"number": "INC100012", "short_description": "SSL certificate expired on internal portal", "state": "resolved",    "priority": "2", "category": "software",  "opened_at": _date(25), "resolved_at": _date(24)},
    {"number": "INC100013", "short_description": "Storage array latency spike",                 "state": "open",        "priority": "2", "category": "hardware",  "opened_at": _date(3),  "resolved_at": None},
    {"number": "INC100014", "short_description": "Firewall blocking legitimate traffic",        "state": "in_progress", "priority": "2", "category": "network",   "opened_at": _date(7),  "resolved_at": None},
    {"number": "INC100015", "short_description": "Service account password expired",            "state": "resolved",    "priority": "3", "category": "access",    "opened_at": _date(18), "resolved_at": _date(15)},
    {"number": "INC100016", "short_description": "Monitoring alerts not firing",                "state": "open",        "priority": "2", "category": "software",  "opened_at": _date(2),  "resolved_at": None},
    {"number": "INC100017", "short_description": "Slow queries degrading checkout performance", "state": "in_progress", "priority": "1", "category": "software",  "opened_at": _date(4),  "resolved_at": None},
    {"number": "INC100018", "short_description": "NTP sync failure causing clock drift",        "state": "resolved",    "priority": "3", "category": "network",   "opened_at": _date(30), "resolved_at": _date(28)},
    {"number": "INC100019", "short_description": "API rate limit exceeded by integration",      "state": "open",        "priority": "3", "category": "software",  "opened_at": _date(9),  "resolved_at": None},
    {"number": "INC100020", "short_description": "Physical access card reader offline",         "state": "resolved",    "priority": "4", "category": "hardware",  "opened_at": _date(22), "resolved_at": _date(20)},
]

SLACK_MESSAGES = [
    {"ts": "1717977600.000001", "user": "U1001", "text": "P1 incident INC100001: network switch unresponsive, on-call notified", "channel_id": "C0123456789"},
    {"ts": "1717974000.000002", "user": "U1002", "text": "Reminder: prod deployment window is today at 17:00 UTC, freeze in effect before that", "channel_id": "C0123456789"},
    {"ts": "1717970400.000003", "user": "U1003", "text": "Alert firing: high CPU on prod-db-01, incident INC100003 opened", "channel_id": "C0123456789"},
    {"ts": "1717966800.000004", "user": "U1001", "text": "PROJECT-A-5 is blocked on security team approval, pinging them now", "channel_id": "C0123456789"},
    {"ts": "1717963200.000005", "user": "U1004", "text": "SLA breach warning: INC100005 has been open for 5 days, escalating to P1", "channel_id": "C0123456789"},
    {"ts": "1717959600.000006", "user": "U1002", "text": "Postmortem published for last week's payment outage — link in #postmortems", "channel_id": "C0123456789"},
    {"ts": "1717956000.000007", "user": "U1003", "text": "New P1 incident: PROJECT-C-2 — API gateway returning 502s, incident bridge open", "channel_id": "C0123456789"},
    {"ts": "1717952400.000008", "user": "U1005", "text": "Deployment successful: service-api v2.1.0 to prod, all health checks green", "channel_id": "C0123456789"},
    {"ts": "1717948800.000009", "user": "U1001", "text": "Daily standup in 15 minutes — open items: INC100004, INC100008, PROJECT-B-11", "channel_id": "C0123456789"},
    {"ts": "1717945200.000010", "user": "U1002", "text": "PROJECT-B sprint review at 15:00 today, 3 tickets to demo — all P2 and below", "channel_id": "C0123456789"},
]


def get_jira_issues(project: str | None = None, status: str | None = None, priority: str | None = None) -> list[dict]:
    issues = JIRA_ISSUES
    if project:
        issues = [i for i in issues if i["key"].startswith(project + "-")]
    if status:
        issues = [i for i in issues if i["status"].lower() == status.lower()]
    if priority:
        issues = [i for i in issues if i["priority"] == priority]
    return issues


def get_jira_issue(key: str) -> dict | None:
    for issue in JIRA_ISSUES:
        if issue["key"] == key:
            return issue
    return None


def get_servicenow_incidents(state: str | None = None) -> list[dict]:
    incidents = SERVICENOW_INCIDENTS
    if state:
        incidents = [i for i in incidents if i["state"] == state]
    return incidents


def get_servicenow_incident(number: str) -> dict | None:
    for inc in SERVICENOW_INCIDENTS:
        if inc["number"] == number:
            return inc
    return None


def get_servicenow_stats() -> dict:
    by_priority: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for inc in SERVICENOW_INCIDENTS:
        p = f"P{inc['priority']}"
        by_priority[p] = by_priority.get(p, 0) + 1
        c = inc["category"]
        by_category[c] = by_category.get(c, 0) + 1
    return {"by_priority": by_priority, "by_category": by_category}


def get_slack_messages() -> list[dict]:
    return SLACK_MESSAGES
