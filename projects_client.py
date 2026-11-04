"""Thin client for Later's undocumented Projects API.

Normalises the quirks found in recon (see API_NOTES.md) so nothing downstream sees them:
- ids are path segments, not params (the brief's flat paths 405)
- list is paginated with a fixed page size of 5; list_projects() walks every page
- dates are epoch milliseconds; this client accepts date/datetime/ISO strings and converts
- mark takes a literal "yes"/"no" flag and SETS done, it does not toggle
- only touch bumps updated_at; modify/add/mark/yank do not, so every mutation here touches afterwards
- the API is in memory: after every write the client dumps everything to backups/latest.json (PROJECTS_AUTOBACKUP=0 disables)
- status is a case-sensitive enum
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app"
STATUSES = ("kickoff", "wip", "blocked", "wrapped", "dropped")
PAGE_SIZE = 5
DAY_MS = 86_400_000


class ApiError(Exception):
    def __init__(self, status: int, message: str, path: str):
        super().__init__(f"{status} on {path}: {message}")
        self.status, self.message, self.path = status, message, path


# ---- date helpers ---------------------------------------------------------

def to_ms(value: int | float | str | date | datetime | None) -> int | None:
    """Anything date-like -> epoch ms. Strings: ISO date/datetime. None passes through."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)
    if isinstance(value, date):
        return to_ms(datetime(value.year, value.month, value.day, tzinfo=timezone.utc))
    if isinstance(value, str):
        return to_ms(datetime.fromisoformat(value))
    raise TypeError(f"cannot convert {value!r} to epoch ms")


def from_ms(ms: Any) -> datetime | None:
    """Epoch ms -> aware datetime. Non-numeric (the API stores arbitrary strings) -> None."""
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def now_ms() -> int:
    return int(time.time() * 1000)


# ---- client ---------------------------------------------------------------

class Projects:
    def __init__(self, base_url: str = BASE_URL, timeout: float = 20.0, autobackup: bool | None = None):
        self.http = httpx.Client(base_url=base_url, timeout=timeout)
        # Every mutation ends in touch(); with autobackup on, touch() also dumps the whole API to
        # backups/latest.json. The API is in memory, so this is the only thing standing between a
        # restart and lost work. Set PROJECTS_AUTOBACKUP=0 to turn it off (bulk loads, tests).
        env = os.environ.get("PROJECTS_AUTOBACKUP")
        self.autobackup = autobackup if autobackup is not None else env != "0"
        self.backup_path = Path(os.environ.get("PROJECTS_BACKUP_PATH", "backups/latest.json"))

    def backup(self, path: Path | str | None = None) -> Path:
        """Dump every project and todo to JSON (what restore.py reads)."""
        out = Path(path) if path else self.backup_path
        out.parent.mkdir(parents=True, exist_ok=True)
        projects = self.list_projects()
        out.write_text(json.dumps({"taken_at": datetime.now(timezone.utc).isoformat(), "projects": projects}, indent=1))
        return out

    def _req(self, method: str, path: str, *, json: dict | None = None, params: dict | None = None) -> Any:
        r = self.http.request(method, path, json=json, params=params)
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", r.text)
            except ValueError:
                msg = r.text
            raise ApiError(r.status_code, msg, path)
        return r.json() if r.content else None

    # projects
    def list_projects(self) -> list[dict]:
        """Walk every page (fixed page size 5)."""
        out: list[dict] = []
        offset = 0
        while True:
            page = self._req("GET", "/api/v1/proj", params={"from": offset})
            out.extend(page["projects"])
            offset += PAGE_SIZE
            if len(page["projects"]) < PAGE_SIZE or offset >= page.get("total", 0):
                break
        return out

    def get(self, pid: str) -> dict:
        return self._req("GET", f"/api/v1/proj/{pid}")

    def create(self, title: str, description: str = "", status: str = "kickoff") -> dict:
        self._check_status(status)
        return self._req("POST", "/api/v1/proj/new",
                         json={"title": title, "description": description, "status": status})

    def modify(self, pid: str, *, touch: bool = True, **fields: Any) -> dict:
        """title/description/status are updatable. QUIRK: modify never bumps updated_at, so this
        touches afterwards by default; otherwise Carlos's "changed this week" misses real edits."""
        if "status" in fields:
            self._check_status(fields["status"])
        out = self._req("PUT", f"/api/v1/proj/{pid}/modify", json=fields)
        return self.touch(pid) if touch else out

    def touch(self, pid: str) -> dict:
        """The only call that bumps updated_at. Body is ignored. Also the autobackup hook."""
        out = self._req("POST", f"/api/v1/proj/{pid}/touch")
        if self.autobackup:
            try:
                self.backup()
            except Exception as e:  # a failed backup must never fail the write
                print(f"[projects_client] autobackup failed: {e}")
        return out

    def remove(self, pid: str) -> dict:
        out = self._req("DELETE", f"/api/v1/proj/{pid}/remove")
        if self.autobackup:
            self.backup()
        return out

    # todos
    def items(self, pid: str) -> list[dict]:
        return self._req("GET", f"/api/v1/proj/{pid}/items")["items"]

    # QUIRK: add/mark/yank never bump the project's updated_at either (only touch does),
    # so each one touches afterwards by default. Pass touch=False for bulk loads.

    def add_item(self, pid: str, task: str, who: str = "", by: Any = None, *, touch: bool = True) -> dict:
        body: dict[str, Any] = {"task": task, "who": who}
        if by is not None:
            body["by"] = to_ms(by)
        out = self._req("POST", f"/api/v1/proj/{pid}/items/add", json=body)
        if touch:
            self.touch(pid)
        return out

    def mark(self, pid: str, tid: str, done: bool = True, *, touch: bool = True) -> dict:
        out = self._req("POST", f"/api/v1/proj/{pid}/items/{tid}/mark",
                        json={"flag": "yes" if done else "no"})
        if touch:
            self.touch(pid)
        return out

    def yank(self, pid: str, tid: str, *, touch: bool = True) -> dict:
        out = self._req("DELETE", f"/api/v1/proj/{pid}/items/{tid}/yank")
        if touch:
            self.touch(pid)
        return out

    # ---- helpers the personas need -----------------------------------------

    def find_project(self, needle: str) -> dict | None:
        """Case-insensitive title match: exact first, then substring. Lets Dan say 'the launch project'."""
        projects = self.list_projects()
        n = needle.strip().lower()
        for p in projects:
            if str(p.get("title", "")).lower() == n:
                return p
        hits = [p for p in projects if n in str(p.get("title", "")).lower()]
        return hits[0] if len(hits) == 1 else (hits[0] if hits else None)

    def find_item(self, pid: str, needle: str) -> dict | None:
        n = needle.strip().lower()
        hits = [t for t in self.items(pid) if n in str(t.get("task", "")).lower()]
        return hits[0] if hits else None

    def overdue(self, as_of: int | None = None) -> list[dict]:
        """Open todos whose due date is in the past. Each row carries its project."""
        now = as_of or now_ms()
        rows = []
        for p in self.list_projects():
            for t in p.get("items") or self.items(p["id"]):
                due = from_ms(t.get("by"))
                if not t.get("done") and due is not None and to_ms(due) < now:
                    rows.append({**t, "project_id": p["id"], "project_title": p["title"]})
        return rows

    def summary(self, days: int = 7, stuck_days: int = 7) -> list[dict]:
        """One row per project for Carlos: state, counts, overdue, stuck, changed-this-week."""
        now = now_ms()
        rows = []
        for p in self.list_projects():
            items = p.get("items")
            if items is None:
                items = self.items(p["id"])
            open_items = [t for t in items if not t.get("done")]
            overdue = [t for t in open_items
                       if (d := from_ms(t.get("by"))) is not None and to_ms(d) < now]
            updated = from_ms(p.get("updated_at"))
            age_days = (now - to_ms(updated)) / DAY_MS if updated else None
            active = p.get("status") in ("kickoff", "wip", "blocked")
            rows.append({
                "id": p["id"],
                "title": p["title"],
                "status": p.get("status"),
                "open": len(open_items),
                "done": len(items) - len(open_items),
                "overdue": len(overdue),
                "updated_at": updated,
                "changed_this_week": age_days is not None and age_days <= days,
                "stuck": active and (
                    p.get("status") == "blocked"
                    or len(overdue) > 0
                    or (age_days is not None and age_days > stuck_days and len(open_items) > 0)
                ),
            })
        return rows

    @staticmethod
    def _check_status(status: str) -> None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {status!r}")


if __name__ == "__main__":
    import json
    api = Projects()
    for row in api.summary():
        print(json.dumps({k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()}))
