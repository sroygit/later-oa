"""Andy's shim: a no-code-friendly HTTP surface for Zapier / Make / n8n / Gumloop.

Why it exists: the real API needs ids as path segments and a literal "yes"/"no" flag, which
no-code tools handle badly. This shim takes names instead of ids and accepts query string,
form, or JSON, so a "Webhooks by Zapier" step with two fields just works.

It also serves Betty's single-file UI at / (see the /ui/ routes at the bottom) and Dan's
MCP server over streamable HTTP at /mcp (mounted at the bottom from mcp_server.py), so
`uvicorn webhook:app` is the only process any of the three personas needs.

Run:   .venv/bin/uvicorn webhook:app --port 8787
Expose to Zapier:  ngrok http 8787   (or cloudflared tunnel --url http://localhost:8787)
See ZAPIER.md for the exact step config.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

from dates import parse_due
from mcp_server import mcp
from projects_client import STATUSES, ApiError, Projects, from_ms

# fastmcp's streamable-http transport needs its own lifespan to run (session manager,
# task group), so FastAPI has to adopt it; without this every /mcp request 500s.
mcp_app = mcp.http_app(path="/mcp")

app = FastAPI(title="Later Projects webhook shim", lifespan=mcp_app.lifespan)
api = Projects()


def due_ms(value) -> int | None:
    """Due-date text -> epoch ms. Empty is fine (no due date); garbage is a 400."""
    if value is None or str(value).strip() == "":
        return None
    ms = parse_due(value)
    if ms is None:
        raise HTTPException(400, f"could not parse due date: {str(value)!r}")
    return ms


async def params(req: Request) -> dict[str, Any]:
    """Merge query string, form body, and JSON body. Query wins on conflict."""
    out: dict[str, Any] = {}
    ct = req.headers.get("content-type", "")
    if "json" in ct:
        try:
            out.update(await req.json() or {})
        except ValueError:
            pass
    elif "form" in ct:
        out.update(dict(await req.form()))
    out.update(dict(req.query_params))
    return out


def resolve_project(name: str) -> dict:
    p = api.get(name) if name.startswith("proj_") else api.find_project(name)
    if not p:
        raise HTTPException(404, f"no project matching {name!r}")
    return p


def resolve_todo(pid: str, name: str) -> dict:
    t = {"id": name} if name.startswith("todo_") else api.find_item(pid, name)
    if not t:
        raise HTTPException(404, f"no todo matching {name!r}")
    return t


@app.api_route("/complete", methods=["GET", "POST"])
async def complete(req: Request):
    """Mark a todo done. Fields: project (title or id), todo (text fragment or id), done (optional, default yes)."""
    q = await params(req)
    if "project" not in q or "todo" not in q:
        raise HTTPException(400, "need project and todo")
    p = resolve_project(q["project"])
    t = resolve_todo(p["id"], q["todo"])
    done = str(q.get("done", "yes")).lower() not in ("no", "false", "0")
    try:
        return {"ok": True, "project": p["title"], "todo": api.mark(p["id"], t["id"], done)}
    except ApiError as e:
        raise HTTPException(e.status, e.message)


@app.api_route("/add", methods=["GET", "POST"])
async def add(req: Request):
    """Add a todo. Fields: project, task, who (optional), due (optional - ISO date or
    natural language like "Friday", "tomorrow", "in 2 weeks")."""
    q = await params(req)
    if "project" not in q or "task" not in q:
        raise HTTPException(400, "need project and task")
    p = resolve_project(q["project"])
    by = due_ms(q.get("due"))
    try:
        return {"ok": True, "project": p["title"],
                "todo": api.add_item(p["id"], q["task"], who=q.get("who", ""), by=by)}
    except (ApiError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/late")
def late():
    """Overdue open todos. Poll this from a Zapier/Make schedule trigger."""
    return api.overdue()


@app.get("/projects")
def projects():
    return [{"id": p["id"], "title": p["title"], "status": p["status"]} for p in api.list_projects()]


# ---- Betty's UI: one HTML page served from this origin, plus JSON under /ui/ ----
# The Projects API sends no CORS headers, so a file:// page cannot call it. Serving
# betty.html from here makes every fetch below same-origin. Andy's routes above are
# untouched; everything new lives under /ui/.

HERE = Path(__file__).resolve().parent


def iso_date(value: Any) -> str | None:
    """datetime or epoch-ms -> 'YYYY-MM-DD'. Unparseable (the API stores raw strings) -> None."""
    d = value if isinstance(value, datetime) else from_ms(value)
    return d.date().isoformat() if d else None


def ui_project(p: dict) -> dict:
    """Project as the page wants it: title always a string, dates pre-formatted."""
    return {
        "id": p["id"],
        "title": str(p.get("title", "")),
        "description": p.get("description") or "",
        "status": p.get("status"),
        "updated": iso_date(p.get("updated_at")),
        "items": [
            {
                "id": t["id"],
                "task": str(t.get("task", "")),
                "who": str(t.get("who") or ""),
                "done": bool(t.get("done")),
                "due": iso_date(t.get("by")),
            }
            for t in (p.get("items") or [])
        ],
    }


def guard(fn):
    """ApiError/ValueError -> HTTP 400/404 with the API's own message."""
    try:
        return fn()
    except ApiError as e:
        raise HTTPException(e.status if e.status in (400, 404) else 400, e.message)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/", include_in_schema=False)
def home():
    """Betty's page. Open http://localhost:8787 after starting this shim."""
    return FileResponse(HERE / "betty.html", media_type="text/html")


@app.get("/ui/projects")
def ui_projects():
    return [ui_project(p) for p in guard(api.list_projects)]


@app.get("/ui/summary")
def ui_summary():
    rows = guard(api.summary)
    late = guard(api.overdue)
    return {
        "statuses": list(STATUSES),
        "rows": [{**r, "updated_at": iso_date(r["updated_at"])} for r in rows],
        "overdue": [
            {
                "id": t["id"],
                "task": str(t.get("task", "")),
                "who": str(t.get("who") or ""),
                "due": iso_date(t.get("by")),
                "project_id": t["project_id"],
                "project_title": str(t["project_title"]),
            }
            for t in late
        ],
    }


@app.post("/ui/projects")
async def ui_create(req: Request):
    q = await params(req)
    title = str(q.get("title", "")).strip()
    if not title:
        raise HTTPException(400, "title is required")
    return ui_project(guard(lambda: api.create(
        title, str(q.get("description") or ""), str(q.get("status") or "kickoff"))))


@app.post("/ui/projects/{pid}/status")
async def ui_status(pid: str, req: Request):
    q = await params(req)
    if not q.get("status"):
        raise HTTPException(400, "status is required")
    return guard(lambda: api.modify(pid, status=str(q["status"])))


@app.post("/ui/projects/{pid}/todos")
async def ui_add_todo(pid: str, req: Request):
    q = await params(req)
    task = str(q.get("task", "")).strip()
    if not task:
        raise HTTPException(400, "task is required")
    by = due_ms(q.get("due"))
    return guard(lambda: api.add_item(pid, task, who=str(q.get("who") or ""), by=by))


@app.post("/ui/projects/{pid}/todos/{tid}/done")
async def ui_mark_todo(pid: str, tid: str, req: Request):
    q = await params(req)
    done = str(q.get("done", True)).lower() not in ("no", "false", "0", "none", "")
    return guard(lambda: api.mark(pid, tid, done))


@app.delete("/ui/projects/{pid}/todos/{tid}")
def ui_yank_todo(pid: str, tid: str):
    return guard(lambda: api.yank(pid, tid))


# ---- Dan's MCP server, same process ----------------------------------------
# mcp_server.py still runs standalone over stdio (`python mcp_server.py`, which is what
# .mcp.json uses); this mount exposes the same nine tools over streamable HTTP at /mcp:
#   claude mcp add --transport http later-projects-http http://localhost:8787/mcp
# Mounted last so every route above keeps precedence over the catch-all mount.
app.mount("/", mcp_app)
