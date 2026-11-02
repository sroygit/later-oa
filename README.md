# Later Projects API — four personas, one client

Take-home for Later's AI Automation Engineer role. 1.5 hour cap. See `DECISIONS.md` for what was built, skipped, and why; `API_NOTES.md` for the docs the API never had.

## Setup

```
uv venv --python 3.12 --managed-python .venv
uv pip install --python .venv/bin/python httpx fastmcp streamlit fastapi uvicorn python-multipart dateparser
```

(macOS: Apple's and Homebrew's Pythons both crashed on fastmcp's HMAC call; the uv-managed build works.)

## The pieces

| Who | What | Run |
|---|---|---|
| everyone | `projects_client.py` — thin wrapper, normalises every quirk | `.venv/bin/python projects_client.py` prints a summary |
| Dan | `mcp_server.py` — 9 MCP tools (add todo, complete, what's late, summary...). Due dates take natural language (`dates.py`): "Friday", "tomorrow", "in 2 weeks". Served two ways from the same module — stdio, or mounted at `/mcp` inside the shim below, one process for all three personas | registered in `.mcp.json` (stdio); open Claude Code here, approve the server when prompted, ask "what's late?". <br> HTTP instead: start the shim, then `claude mcp add --transport http later-projects-http http://localhost:8787/mcp` |
| Carlos | `digest.py` — weekly digest, markdown or Slack. Change detection is snapshot-based (`snapshots.py` stores each run's full project list in `snapshots.sqlite` and diffs it), not `updated_at`, which only moves on `touch` — so edits made outside this client still show up. `--days N` sets the window. | `.venv/bin/python digest.py [--slack] [--days 7]` |
| Betty | `betty.html` — one self-contained HTML file, served by the shim so it can call the API (the API sends no CORS headers, so a `file://` page can't) | `.venv/bin/uvicorn webhook:app --port 8787`, then open <http://localhost:8787> |
| Betty (earlier) | `app.py` — the first version, Streamlit. Kept for reference; `betty.html` replaces it | `.venv/bin/streamlit run app.py` |
| everyone | `dates.py` — `parse_due(text)` -> epoch ms. ISO, epoch ms, or natural language ("Friday" = the *next* Friday, never today; "in 3 days", "end of month", "Nov 7"); every date-only answer is pinned to midnight UTC | `.venv/bin/python dates.py` prints the parse table |
| anyone | `backup.py` / `restore.py` — the API is in memory. The client also auto-dumps to `backups/latest.json` after every write (`PROJECTS_AUTOBACKUP=0` to disable). `seed_backup.json` is the 7-project seed state from 2026-11-02. | `.venv/bin/python restore.py backups/latest.json` after a reset |
| Andy | `webhook.py` + `ZAPIER.md` — name-based shim for no-code tools; `due` accepts whatever the trigger said ("next Friday"), unparseable text is a 400. One process: this app also serves Betty's page at `/` and Dan's MCP server at `/mcp` | `.venv/bin/uvicorn webhook:app --port 8787` — serves the UI, the webhook routes, and MCP over HTTP |

## One process

`uvicorn webhook:app --port 8787` is everything Betty, Andy and Dan need:

| Path | Who |
|---|---|
| `/` | Betty's UI (plus the JSON it reads under `/ui/`) |
| `/add`, `/complete`, `/late`, `/projects` | Andy's no-code shim |
| `/mcp` | Dan's MCP server, streamable HTTP |

`mcp_server.py` is still the module that defines the tools and still runs standalone over
stdio, which is what `.mcp.json` registers and what the project has been used with in
Claude Code. The HTTP transport is the alternative, not the replacement:

```
# stdio (default, in .mcp.json):
claude mcp add later-projects -- "$PWD/.venv/bin/python" "$PWD/mcp_server.py"

# http, against the running shim:
claude mcp add --transport http later-projects-http http://localhost:8787/mcp
```

## How the API was reverse-engineered

Two-tier agent system, see `recon/`: four Sonnet probers in parallel wrote raw findings, a Fable synthesizer wrote `API_NOTES.md`, a Fable reviewer rewrote the prober's prompt from what went wrong (`recon/PROMPT_CHANGELOG.md`), then a narrower second round. Every agent run is in `recon/RUNLOG.md`.
