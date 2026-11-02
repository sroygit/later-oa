# Later Projects API — four personas, one client

Take-home for Later's AI Automation Engineer role. 1.5 hour cap. See `DECISIONS.md` for what was built, skipped, and why; `API_NOTES.md` for the docs the API never had.

## Setup

```
uv venv --python 3.12 --managed-python .venv
uv pip install --python .venv/bin/python httpx fastmcp streamlit fastapi uvicorn python-multipart
```

(macOS: Apple's and Homebrew's Pythons both crashed on fastmcp's HMAC call; the uv-managed build works.)

## The pieces

| Who | What | Run |
|---|---|---|
| everyone | `projects_client.py` — thin wrapper, normalises every quirk | `.venv/bin/python projects_client.py` prints a summary |
| Dan | `mcp_server.py` — 9 MCP tools (add todo, complete, what's late, summary...) | registered in `.mcp.json`; open Claude Code here and ask "what's late?" |
| Carlos | `digest.py` — weekly digest, markdown or Slack | `.venv/bin/python digest.py [--slack]` |
| Betty | `app.py` — Streamlit UI, hand-off-able | `.venv/bin/streamlit run app.py` |
| Andy | `webhook.py` + `ZAPIER.md` — name-based shim for no-code tools | `.venv/bin/uvicorn webhook:app --port 8787` |

## How the API was reverse-engineered

Two-tier agent system, see `recon/`: four Sonnet probers in parallel wrote raw findings, a Fable synthesizer wrote `API_NOTES.md`, a Fable reviewer rewrote the prober's prompt from what went wrong (`recon/PROMPT_CHANGELOG.md`), then a narrower second round. Every agent run is in `recon/RUNLOG.md`.
