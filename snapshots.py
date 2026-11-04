"""Snapshot store + differ, so "what changed" doesn't depend on the API's `updated_at`.

Recon proved `updated_at` moves on exactly one call, `POST .../touch` (API_NOTES.md, first
Quirk). Our client touches after every mutation, but anything written to the API another
way leaves `updated_at` frozen. So the digest keeps its own history: one row per run holding
the full `list_projects()` JSON, and change is computed by diffing two rows.

    from snapshots import SnapshotStore, diff
    store = SnapshotStore()
    cur = store.take(api.list_projects())
    base = store.oldest_within(days=7, epoch=cur["epoch"])
    changes = diff(base["projects"], cur["projects"])

Epochs guard against the shared take-home API being reset under us: if a snapshot shares no
project ids with its predecessor, or the project count falls below the 7 seed projects, it
starts a new epoch and is never diffed against anything older.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots.sqlite")
SEED_COUNT = 7  # seed projects that pre-exist; see API_NOTES.md "Seed data"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    taken_at TEXT    NOT NULL,          -- ISO-8601 UTC
    epoch   INTEGER NOT NULL,           -- bumped when the API looks reset; never diff across
    total   INTEGER NOT NULL,           -- project count at snapshot time
    payload TEXT    NOT NULL            -- full list_projects() JSON, items embedded
);
CREATE INDEX IF NOT EXISTS snapshots_taken_at ON snapshots (epoch, taken_at);
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SnapshotStore:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # ---- writing ----------------------------------------------------------

    def take(self, projects: list[dict], taken_at: datetime | None = None) -> dict:
        """Store one snapshot of the whole portfolio. Returns the stored row (decoded)."""
        ts = (taken_at or _utcnow()).astimezone(timezone.utc)
        total = len(projects)
        prev = self.latest()
        epoch = 1 if prev is None else prev["epoch"]
        reset = None
        if prev is not None:
            if not (_ids(prev["projects"]) & _ids(projects)):
                reset = "no project ids in common with the previous snapshot"
            elif total < SEED_COUNT:
                reset = f"project count {total} fell below the {SEED_COUNT} seed projects"
            if reset:
                epoch = prev["epoch"] + 1
        cur = self.db.execute(
            "INSERT INTO snapshots (taken_at, epoch, total, payload) VALUES (?, ?, ?, ?)",
            (ts.isoformat(), epoch, total, json.dumps(projects, sort_keys=True)),
        )
        self.db.commit()
        row = self._row(cur.lastrowid)
        row["reset_reason"] = reset
        return row

    # ---- reading ----------------------------------------------------------

    def latest(self, epoch: int | None = None) -> dict | None:
        sql = "SELECT * FROM snapshots"
        args: tuple = ()
        if epoch is not None:
            sql += " WHERE epoch = ?"
            args = (epoch,)
        sql += " ORDER BY taken_at DESC, id DESC LIMIT 1"
        return self._decode(self.db.execute(sql, args).fetchone())

    def latest_before(self, ts: datetime | str, epoch: int | None = None) -> dict | None:
        """Most recent snapshot strictly older than `ts` (same epoch if given)."""
        sql = "SELECT * FROM snapshots WHERE taken_at < ?"
        args: list[Any] = [_iso(ts)]
        if epoch is not None:
            sql += " AND epoch = ?"
            args.append(epoch)
        sql += " ORDER BY taken_at DESC, id DESC LIMIT 1"
        return self._decode(self.db.execute(sql, args).fetchone())

    def oldest_within(self, days: float, epoch: int | None = None,
                      now: datetime | None = None, before_id: int | None = None) -> dict | None:
        """Oldest snapshot inside the last `days` — the baseline for "changed this week".

        `before_id` excludes the run's own just-taken snapshot, so a first run in the window
        yields None and the caller can fall back to `updated_at`.
        """
        cutoff = (now or _utcnow()).astimezone(timezone.utc) - timedelta(days=days)
        sql = "SELECT * FROM snapshots WHERE taken_at >= ?"
        args: list[Any] = [cutoff.isoformat()]
        if epoch is not None:
            sql += " AND epoch = ?"
            args.append(epoch)
        if before_id is not None:
            sql += " AND id < ?"
            args.append(before_id)
        sql += " ORDER BY taken_at ASC, id ASC LIMIT 1"
        return self._decode(self.db.execute(sql, args).fetchone())

    def count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]

    # ---- internals --------------------------------------------------------

    def _row(self, rowid: int) -> dict:
        return self._decode(self.db.execute("SELECT * FROM snapshots WHERE id = ?", (rowid,)).fetchone())

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "taken_at": datetime.fromisoformat(row["taken_at"]),
            "epoch": row["epoch"],
            "total": row["total"],
            "projects": json.loads(row["payload"]),
        }


def _iso(ts: datetime | str) -> str:
    return ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts


def _ids(projects: Iterable[dict]) -> set[str]:
    return {str(p.get("id")) for p in projects if p.get("id")}


# ---- the diff -------------------------------------------------------------

def _items(project: dict) -> dict[str, dict]:
    return {str(t.get("id")): t for t in (project.get("items") or []) if t.get("id")}


def _due(value: Any) -> str:
    """Render a todo's `by` for humans. The API stores any JSON value verbatim."""
    if value is None or value == "":
        return "none"
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return str(value)


def _who(todo: dict) -> str:
    who = todo.get("who")
    return str(who) if who not in (None, "") else "unassigned"


def _short(text: Any, n: int = 60) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def diff(old_projects: list[dict], new_projects: list[dict]) -> dict:
    """Specific, human-readable change items between two snapshots.

    Returns {"items": [...], "counts": {kind: n}, "by_project": {title: [item, ...]},
             "project_ids": {pid, ...}}. Each item has kind/project_id/project_title/text.
    """
    old = {str(p.get("id")): p for p in old_projects}
    new = {str(p.get("id")): p for p in new_projects}
    items: list[dict] = []

    def add(kind: str, project: dict, text: str) -> None:
        items.append({
            "kind": kind,
            "project_id": str(project.get("id")),
            "project_title": str(project.get("title")),
            "text": text,
        })

    for pid in new.keys() - old.keys():
        p = new[pid]
        todos = list(_items(p).values())
        add("project_created", p,
            f"project created [{p.get('status')}]" + (f" with {len(todos)} todo(s)" if todos else ""))
        for t in todos:  # a new project's todos are new too; name them
            suffix = " (already done)" if t.get("done") else ""
            add("todo_added", p, f"todo added: \"{_short(t.get('task'))}\" "
                                 f"({_who(t)}, due {_due(t.get('by'))}){suffix}")

    for pid in old.keys() - new.keys():
        add("project_removed", old[pid], "project removed")

    for pid in sorted(old.keys() & new.keys()):
        o, n = old[pid], new[pid]
        if str(o.get("title")) != str(n.get("title")):
            add("project_renamed", n, f"renamed from \"{_short(o.get('title'))}\"")
        if o.get("status") != n.get("status"):
            add("project_status_changed", n, f"status {o.get('status')} → {n.get('status')}")
        if str(o.get("description") or "") != str(n.get("description") or ""):
            old_d, new_d = str(o.get("description") or ""), str(n.get("description") or "")
            if not old_d:
                add("project_description_changed", n, f"description set to \"{_short(new_d)}\"")
            elif not new_d:
                add("project_description_changed", n, "description cleared")
            else:
                add("project_description_changed", n, f"description changed to \"{_short(new_d)}\"")

        o_items, n_items = _items(o), _items(n)
        for tid in n_items.keys() - o_items.keys():
            t = n_items[tid]
            suffix = " (already done)" if t.get("done") else ""
            add("todo_added", n, f"todo added: \"{_short(t.get('task'))}\" ({_who(t)}, due {_due(t.get('by'))}){suffix}")
        for tid in o_items.keys() - n_items.keys():
            t = o_items[tid]
            add("todo_removed", n, f"todo removed: \"{_short(t.get('task'))}\"")
        for tid in sorted(o_items.keys() & n_items.keys()):
            ot, nt = o_items[tid], n_items[tid]
            task = _short(nt.get("task"))
            if bool(ot.get("done")) != bool(nt.get("done")):
                kind = "todo_completed" if nt.get("done") else "todo_reopened"
                verb = "completed" if nt.get("done") else "reopened"
                add(kind, n, f"todo {verb}: \"{task}\"")
            if str(ot.get("task") or "") != str(nt.get("task") or ""):
                add("todo_renamed", n, f"todo reworded: \"{_short(ot.get('task'))}\" → \"{task}\"")
            if str(ot.get("who") or "") != str(nt.get("who") or ""):
                add("todo_reassigned", n, f"todo \"{task}\" reassigned {_who(ot)} → {_who(nt)}")
            if ot.get("by") != nt.get("by"):
                add("todo_due_changed", n, f"todo \"{task}\" due {_due(ot.get('by'))} → {_due(nt.get('by'))}")

    counts: dict[str, int] = {}
    by_project: dict[str, list[dict]] = {}
    for it in items:
        counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        by_project.setdefault(it["project_title"], []).append(it)
    return {
        "items": items,
        "counts": counts,
        "by_project": by_project,
        "project_ids": {it["project_id"] for it in items},
    }


if __name__ == "__main__":
    from projects_client import Projects

    store = SnapshotStore()
    row = store.take(Projects().list_projects())
    print(f"snapshot #{row['id']} epoch {row['epoch']} at {row['taken_at'].isoformat()} "
          f"({row['total']} projects, {store.count()} snapshots stored)")
    if row.get("reset_reason"):
        print(f"new epoch: {row['reset_reason']}")
