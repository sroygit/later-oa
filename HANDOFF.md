# Later AI Automation Engineer Take-Home — Handoff

Source: `Later_AI_Co-op_Takehome_Brief_(2)_(1)_(1).pdf` in this folder (run `pdftotext -layout <file> -` to re-read).

## Status
- Brief read and summarized (below). No code written yet.
- API liveness NOT yet confirmed — the previous session's sandbox had no outbound network. First step: probe it from this terminal.
- 1.5h hard-cap clock has NOT started. Everything below is pre-clock planning.

## The brief in short
- Later hosts an undocumented, in-memory **Projects API** at
  `https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app`
  Projects: title, description, status, todos, updated_at. Todos: person + due date.
  No docs/SDK/UI. Has deliberate quirks — discovering them is part of the task. Resets on restart.
- Endpoints (no param/payload shapes given):
  - GET  /api/v1/health
  - GET  /api/v1/proj            (list)
  - POST /api/v1/proj/new
  - GET  /api/v1/proj/           (single? — note trailing slash; probably takes an id param)
  - PUT  /api/v1/proj/modify
  - DELETE /api/v1/proj/remove
  - POST /api/v1/proj/touch      (bump updated_at?)
  - GET  /api/v1/proj/items
  - POST /api/v1/proj/items/add
  - POST /api/v1/proj/items/mark (complete a todo)
  - DELETE /api/v1/proj/items/yank
- Four non-technical personas to enable:
  1. **Andy** — Zapier/Make/n8n/Gumloop. External triggers → mark todos complete.
  2. **Betty** — light vibe-coder. Wants a nicer-than-curl UI she can hand to teammates.
  3. **Carlos** — manager. Summary of all projects: state, what's stuck, what changed this week (UI / weekly email / Slack post).
  4. **Dan** — talk to projects via LLM ("add a todo to launch project for Friday, assign to me", "what's late?").
- Rules: 1.5h HARD cap. Runs on your machine, demoed live. Grading is on *choices* — what you built, skipped, and would do with a full day. Not graded: tests, auth, observability, clean code, finishing. Skipping a persona is fine if you can defend it.

## Proposed plan (time-boxed)
**0–15 min — Reverse-engineer the API.** Hit every endpoint with curl; try query params vs JSON body vs form; note status codes, error messages, id format, date format, and any quirks (e.g. odd field names, pagination, trailing-slash behaviour, case sensitivity, "mark" toggling vs setting). Write findings to `API_NOTES.md` as you go — this doubles as the docs Later never gave you and is demo material.

**15–45 min — One thin client layer that serves everyone.** A small typed Python (or TS) wrapper `projects_client.py` with clean functions: list_projects, get_project, create, update, touch, delete, list_todos, add_todo, mark_todo, remove_todo, plus helpers like `overdue()`, `changed_since(date)`, `summary()`. Normalise the quirks here so nothing downstream sees them.

**45–75 min — Expose the wrapper for the personas (pick order by leverage):**
- **Dan (LLM):** wrap the client as an MCP server (fastmcp) → works in Claude Desktop/Code immediately. Highest leverage: also gives Carlos a "summarise my projects" tool for free.
- **Carlos (summary):** `summary()` in the client → a one-command markdown/Slack-formatted digest (stuck = no todo touched in N days / overdue todos; changed this week = updated_at within 7d). Cron/weekly is a one-liner, mention rather than build.
- **Betty (UI):** Streamlit or a single HTML page over the client. Cheap, hand-off-able. Do last / stub if out of time.
- **Andy (Zapier):** likely needs a *webhook-friendly* endpoint (Zapier can call REST directly, but quirks + weird verbs like DELETE-with-body break no-code tools). A tiny FastAPI shim `/complete?project=..&todo=..` that accepts GET/POST with simple params + a short "paste this into Zapier Webhooks" doc. Could skip and explain: "Zapier can hit the raw API; here's the exact Webhooks step config."

**75–90 min — Stop. Write `DECISIONS.md`:** what you built, what you skipped and why, quirks found, what you'd do with a full day.

## Demo talking points to keep in mind
- One wrapper → four surfaces is the design argument.
- The API notes are a deliverable (they said "no docs").
- Be explicit about trade-offs and what you'd skip.
