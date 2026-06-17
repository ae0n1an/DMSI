# IT Operations Chatbot

A Streamlit chatbot for querying Jira, Slack, and ServiceNow data. Supports live API connections or mock data for development, and a persistent xlsx-backed data store for ServiceNow.

## Setup

```bash
cd chatbot
pip install -r requirements.txt
cp .env.example .env  # fill in your credentials
streamlit run app.py
```

Set `USE_MOCK_DATA=true` in `.env` to run without live connections.

## ServiceNow Data

The chatbot loads ServiceNow data from an exported xlsx file stored in a local SQLite database (`data/servicenow.db`). To upload or replace the data, start the app with `DEV_MODE=true`:

```bash
DEV_MODE=true streamlit run app.py
```

A file uploader appears in the sidebar under **ServiceNow Data**. Upload your xlsx export once — the data persists across restarts and is available to all users without re-uploading.

## Example Queries

### Priority summary

> **"Summarise all tickets by priority"**

Returns an L1–L4 breakdown with counts by state (open, in progress, resolved) and renders a grouped bar chart.

---

> **"How many L1 tickets are currently open?"**

Filters the priority summary to L1 and open state.

---

> **"Show me a chart of tickets by priority and state"**

Explicitly requests the priority summary bar chart.

### Time in stage

> **"How long does it take to resolve L1 tickets on average?"**

Returns average queue time (created → work start), resolution time (work start → closed), and total time for L1, with a stage time bar chart.

---

> **"What's the average resolution time across all priority levels?"**

Returns the stage breakdown for L1–L4 side by side so you can compare.

---

> **"Which priority level spends the most time in the queue before work starts?"**

Compares queue time across priorities and highlights the longest.

### Ticket lookup by ID

> **"Show me the details of INC0012345"**

Returns all fields for that ticket — description, state, priority, assignment group, timestamps, resolution notes, etc.

---

> **"What's the status of INC0098765?"**

Quick state and priority check on a single ticket.

### Filtered lists

> **"List all open L1 tickets"**

Returns a numbered list of open priority-1 tickets with short descriptions.

---

> **"Show me all tickets assigned to the Network Ops group"**

Filters by assignment group across all states and priorities.

---

> **"What P2 tickets were resolved this month?"**

Filters by priority 2 and resolved state; you can refine further with a date range.

---

> **"Show me the 10 most recent open tickets"**

Returns the latest open tickets ordered by created date.

### Ad-hoc queries

> **"How many tickets does each assignment group have open right now?"**

Uses the SQL fallback tool to group by assignment group where state = 'open'.

---

> **"Which configuration items have the most incidents?"**

Groups by configuration_item and counts — useful for spotting problem areas.

---

> **"Show me all tickets tagged with 'network' that are still open"**

Queries the tags column with a filter on state.

---

> **"What percentage of L1 tickets were resolved within 24 hours?"**

Combines stage time data with a count query to calculate SLA adherence.

## Running Tests

```bash
cd chatbot
pytest tests/ -v
```
