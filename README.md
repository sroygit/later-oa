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
| Dan | `mcp_server.py` — 9 MCP tools (add todo, complete, what's late, summary...) | registered in `.mcp.json`; open Claude Code here, approve the server when prompted, ask "what's late?" |
| Carlos | `digest.py` — weekly digest, markdown or Slack. Change detection is snapshot-based (`snapshots.py` stores each run's full project list in `snapshots.sqlite` and diffs it), not `updated_at`, which only moves on `touch` — so edits made outside this client still show up. `--days N` sets the window. | `.venv/bin/python digest.py [--slack] [--days 7]` |
| Betty | `betty.html` — one self-contained HTML file, served by the shim so it can call the API (the API sends no CORS headers, so a `file://` page can't) | `.venv/bin/uvicorn webhook:app --port 8787`, then open <http://localhost:8787> |
| Betty (earlier) | `app.py` — the first version, Streamlit. Kept for reference; `betty.html` replaces it | `.venv/bin/streamlit run app.py` |
| anyone | `backup.py` / `restore.py` — the API is in memory; dump to JSON, replay after a reset | `.venv/bin/python backup.py` then `.venv/bin/python restore.py backups/<file>.json` |
| Andy | `webhook.py` + `ZAPIER.md` — name-based shim for no-code tools | `.venv/bin/uvicorn webhook:app --port 8787` |

## How the API was reverse-engineered

Two-tier agent system, see `recon/`: four Sonnet probers in parallel wrote raw findings, a Fable synthesizer wrote `API_NOTES.md`, a Fable reviewer rewrote the prober's prompt from what went wrong (`recon/PROMPT_CHANGELOG.md`), then a narrower second round. Every agent run is in `recon/RUNLOG.md`.
