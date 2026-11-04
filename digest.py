"""Carlos's weekly digest. One command, markdown out (pipe to Slack, email, or just read it).

    .venv/bin/python digest.py              # markdown
    .venv/bin/python digest.py --slack      # Slack mrkdwn
    .venv/bin/python digest.py --days 14    # window for "changed" / "stuck" (default 7)
Cron it weekly:  0 9 * * MON  cd "<this dir>" && .venv/bin/python digest.py --slack | <your slack webhook poster>

Change detection does NOT use the API's `updated_at`: recon proved only `POST .../touch`
moves it, so anything written to the API outside our client leaves it frozen (API_NOTES.md,
first Quirk). Instead every run snapshots the full project list to `snapshots.sqlite` and
diffs against the oldest snapshot inside the window. `updated_at` survives only as the
first-run fallback, and the digest says so when it falls back.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from projects_client import DAY_MS, Projects, from_ms, now_ms, to_ms
from snapshots import SnapshotStore, diff

STATUS_ICON = {"kickoff": "🟡", "wip": "🟢", "blocked": "🔴", "wrapped": "✅", "dropped": "⚫"}
ACTIVE = ("kickoff", "wip", "blocked")
KIND_LABEL = {
    "project_created": "new", "project_removed": "removed", "project_renamed": "renamed",
    "project_status_changed": "status", "project_description_changed": "description",
    "todo_added": "todo", "todo_completed": "done", "todo_reopened": "reopened",
    "todo_removed": "todo gone", "todo_renamed": "todo", "todo_reassigned": "owner",
    "todo_due_changed": "due",
}


def _rows(projects: list[dict], changed_ids: set[str] | None, days: int) -> list[dict]:
    """One row per project. `changed_ids` is None when we have no snapshot baseline."""
    now = now_ms()
    rows = []
    for p in projects:
        items = p.get("items") or []
        open_items = [t for t in items if not t.get("done")]
        overdue = [t for t in open_items
                   if (d := from_ms(t.get("by"))) is not None and to_ms(d) < now]
        updated = from_ms(p.get("updated_at"))
        age_days = (now - to_ms(updated)) / DAY_MS if updated else None
        if changed_ids is None:  # first run in the window: fall back to updated_at
            changed = age_days is not None and age_days <= days
        else:
            changed = str(p["id"]) in changed_ids
        rows.append({
            "id": str(p["id"]), "title": str(p.get("title")), "status": p.get("status"),
            "open": len(open_items), "done": len(items) - len(open_items),
            "overdue": overdue, "updated_at": updated, "changed_this_week": changed,
            "stuck": p.get("status") in ACTIVE and (
                p.get("status") == "blocked"
                or len(overdue) > 0
                or (not changed and len(open_items) > 0)
            ),
        })
    return rows


def build(days: int = 7, slack: bool = False) -> str:
    api = Projects()
    store = SnapshotStore()
    projects = api.list_projects()
    snap = store.take(projects)
    base = store.oldest_within(days=days, epoch=snap["epoch"], before_id=snap["id"])

    changes = diff(base["projects"], projects) if base else None
    rows = _rows(projects, changes["project_ids"] if changes else None, days)

    b = "*" if slack else "**"
    h = (lambda s: f"*{s}*") if slack else (lambda s: f"## {s}")
    today = datetime.now(timezone.utc).date().isoformat()

    out = [h(f"Projects digest — {today}"), ""]
    stuck = [r for r in rows if r["stuck"]]
    changed = [r for r in rows if r["changed_this_week"]]
    late = sorted(
        ({**t, "project_title": r["title"]} for r in rows for t in r["overdue"]),
        key=lambda t: to_ms(from_ms(t.get("by"))) or 0,
    )
    out.append(f"{len(rows)} projects · {len(changed)} changed in the last {days} days · "
               f"{len(stuck)} look stuck · {len(late)} overdue todos")
    if base:
        out.append(f"_Change is measured against the snapshot taken "
                   f"{base['taken_at'].strftime('%Y-%m-%d %H:%M')}Z, not the API's `updated_at`._")
    else:
        out.append("_No earlier snapshot in this window — first run, using `updated_at`. "
                   "It only moves on `touch`, so changes made outside this client are invisible "
                   "until the next run._")
    out.append("")

    out.append(h("What changed this week"))
    if changes is None:
        out.append("No baseline snapshot yet; this run established one.")
    elif not changes["items"]:
        out.append("Nothing changed since the last snapshot in this window.")
    else:
        summary = ", ".join(f"{n} {KIND_LABEL.get(k, k)}" for k, n in sorted(changes["counts"].items()))
        out.append(f"{len(changes['items'])} changes — {summary}")
        for title, group in sorted(changes["by_project"].items()):
            out.append(f"- {b}{title}{b}")
            for it in group:
                out.append(f"  - {it['text']}")
    out.append("")

    since = (base["taken_at"].strftime("%b %d %H:%MZ") if base else f"{days}+ days ago")
    out.append(h("Needs attention"))
    if not stuck:
        out.append("Nothing looks stuck.")
    for r in stuck:
        why = []
        if r["status"] == "blocked":
            why.append("status is blocked")
        if r["overdue"]:
            why.append(f"{len(r['overdue'])} overdue")
        if not r["changed_this_week"] and r["open"]:
            why.append(f"no change since {since} with {r['open']} open")
        out.append(f"- {STATUS_ICON.get(r['status'], '')} {b}{r['title']}{b} — {', '.join(why)}")
    out.append("")

    out.append(h("Overdue todos"))
    if not late:
        out.append("None.")
    for t in late:
        due = from_ms(t.get("by"))
        due_s = due.date().isoformat() if due else str(t.get("by"))
        out.append(f"- {t['task']} ({t.get('who') or 'unassigned'}, due {due_s}) — {t['project_title']}")
    out.append("")

    out.append(h("All projects"))
    for r in sorted(rows, key=lambda r: (r["status"] != "blocked", not r["changed_this_week"],
                                         -(r["updated_at"].timestamp() if r["updated_at"] else 0))):
        upd = r["updated_at"].date().isoformat() if r["updated_at"] else "?"
        n_changes = len(changes["by_project"].get(r["title"], [])) if changes else 0
        flag = f" 🆕 {n_changes} change(s)" if r["changed_this_week"] and changes else (
            " 🆕" if r["changed_this_week"] else "")
        out.append(f"- {STATUS_ICON.get(r['status'], '')} {b}{r['title']}{b} [{r['status']}] — "
                   f"{r['open']} open / {r['done']} done, touched {upd}{flag}")
    return "\n".join(out)


def _days_arg(argv: list[str]) -> int:
    if "--days" in argv:
        i = argv.index("--days")
        if i + 1 < len(argv):
            return int(argv[i + 1])
        raise SystemExit("--days needs a number")
    for a in argv:
        if a.startswith("--days="):
            return int(a.split("=", 1)[1])
    return 7


if __name__ == "__main__":
    print(build(days=_days_arg(sys.argv), slack="--slack" in sys.argv))
