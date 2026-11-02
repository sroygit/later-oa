"""MCP server over projects_client — lets Dan (and Carlos) talk to projects through any MCP-capable LLM.

Run:  .venv/bin/python mcp_server.py          (stdio transport)
Register in Claude Code:  claude mcp add later-projects -- "$PWD/.venv/bin/python" "$PWD/mcp_server.py"
"""
from __future__ import annotations

from datetime import datetime

from fastmcp import FastMCP

from projects_client import STATUSES, ApiError, Projects, from_ms

mcp = FastMCP("later-projects")
api = Projects()


def _fmt_dt(v) -> str | None:
    d = v if isinstance(v, datetime) else from_ms(v)
    return d.date().isoformat() if d else None


def _todo(t: dict) -> dict:
    return {"id": t["id"], "task": t.get("task"), "who": t.get("who") or None,
            "due": _fmt_dt(t.get("by")), "done": bool(t.get("done"))}


def _project(p: dict, with_items: bool = True) -> dict:
    out = {"id": p["id"], "title": p.get("title"), "status": p.get("status"),
           "description": p.get("description") or None, "updated": _fmt_dt(p.get("updated_at"))}
    if with_items and p.get("items") is not None:
        out["todos"] = [_todo(t) for t in p["items"]]
    return out


def _resolve(project: str) -> dict:
    """Accept an id or a (partial) title."""
    if project.startswith("proj_"):
        return api.get(project)
    p = api.find_project(project)
    if not p:
        titles = [x["title"] for x in api.list_projects()]
        raise ValueError(f"No project matching {project!r}. Known projects: {titles}")
    return p


@mcp.tool
def list_projects() -> list[dict]:
    """List every project with status, last-updated date, and todos."""
    return [_project(p) for p in api.list_projects()]


@mcp.tool
def get_project(project: str) -> dict:
    """Get one project by id (proj_xxxxxx) or by title (partial, case-insensitive)."""
    return _project(_resolve(project))


@mcp.tool
def create_project(title: str, description: str = "", status: str = "kickoff") -> dict:
    """Create a project. status must be one of kickoff, wip, blocked, wrapped, dropped."""
    return _project(api.create(title, description, status))


@mcp.tool
def update_project(project: str, title: str | None = None, description: str | None = None,
                   status: str | None = None) -> dict:
    """Change a project's title, description, or status (kickoff|wip|blocked|wrapped|dropped)."""
    p = _resolve(project)
    fields = {k: v for k, v in dict(title=title, description=description, status=status).items() if v is not None}
    return _project(api.modify(p["id"], **fields))


@mcp.tool
def add_todo(project: str, task: str, due: str | None = None, who: str | None = None) -> dict:
    """Add a todo to a project. due is an ISO date like 2026-11-07 (resolve 'Friday' to a date first).
    who is the person's name; use the user's own name for 'assign it to me'."""
    p = _resolve(project)
    return _todo(api.add_item(p["id"], task, who=who or "", by=due))


@mcp.tool
def complete_todo(project: str, todo: str, done: bool = True) -> dict:
    """Mark a todo done (or not done with done=false). todo is a todo id or a fragment of its text."""
    p = _resolve(project)
    t = api.find_item(p["id"], todo) if not todo.startswith("todo_") else {"id": todo}
    if not t:
        raise ValueError(f"No todo matching {todo!r} in {p['title']!r}")
    return _todo(api.mark(p["id"], t["id"], done))


@mcp.tool
def remove_todo(project: str, todo: str) -> dict:
    """Delete a todo from a project. todo is a todo id or a fragment of its text."""
    p = _resolve(project)
    t = api.find_item(p["id"], todo) if not todo.startswith("todo_") else {"id": todo}
    if not t:
        raise ValueError(f"No todo matching {todo!r} in {p['title']!r}")
    return api.yank(p["id"], t["id"])


@mcp.tool
def whats_late() -> list[dict]:
    """All open todos whose due date has passed, across every project."""
    return [{**_todo(r), "project": r["project_title"], "project_id": r["project_id"]} for r in api.overdue()]


@mcp.tool
def portfolio_summary(days: int = 7) -> list[dict]:
    """Manager view: one row per project with status, open/done counts, overdue count,
    whether it changed in the last `days` days, and whether it looks stuck."""
    rows = api.summary(days=days, stuck_days=days)
    return [{**r, "updated_at": _fmt_dt(r["updated_at"])} for r in rows]


if __name__ == "__main__":
    mcp.run()
