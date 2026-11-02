"""Andy's shim: a no-code-friendly HTTP surface for Zapier / Make / n8n / Gumloop.

Why it exists: the real API needs ids as path segments and a literal "yes"/"no" flag, which
no-code tools handle badly. This shim takes names instead of ids and accepts query string,
form, or JSON, so a "Webhooks by Zapier" step with two fields just works.

Run:   .venv/bin/uvicorn webhook:app --port 8787
Expose to Zapier:  ngrok http 8787   (or cloudflared tunnel --url http://localhost:8787)
See ZAPIER.md for the exact step config.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request

from projects_client import ApiError, Projects

app = FastAPI(title="Later Projects webhook shim")
api = Projects()


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
    """Add a todo. Fields: project, task, who (optional), due (optional ISO date)."""
    q = await params(req)
    if "project" not in q or "task" not in q:
        raise HTTPException(400, "need project and task")
    p = resolve_project(q["project"])
    try:
        return {"ok": True, "project": p["title"],
                "todo": api.add_item(p["id"], q["task"], who=q.get("who", ""), by=q.get("due") or None)}
    except (ApiError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/late")
def late():
    """Overdue open todos. Poll this from a Zapier/Make schedule trigger."""
    return api.overdue()


@app.get("/projects")
def projects():
    return [{"id": p["id"], "title": p["title"], "status": p["status"]} for p in api.list_projects()]
