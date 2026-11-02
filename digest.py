"""Carlos's weekly digest. One command, markdown out (pipe to Slack, email, or just read it).

    .venv/bin/python digest.py            # markdown
    .venv/bin/python digest.py --slack    # Slack mrkdwn
Cron it weekly:  0 9 * * MON  cd "<this dir>" && .venv/bin/python digest.py --slack | <your slack webhook poster>
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from projects_client import Projects

STATUS_ICON = {"kickoff": "🟡", "wip": "🟢", "blocked": "🔴", "wrapped": "✅", "dropped": "⚫"}


def build(days: int = 7, slack: bool = False) -> str:
    api = Projects()
    rows = api.summary(days=days, stuck_days=days)
    late = api.overdue()
    b = "*" if slack else "**"
    h = (lambda s: f"*{s}*") if slack else (lambda s: f"## {s}")
    today = datetime.now(timezone.utc).date().isoformat()

    out = [h(f"Projects digest — {today}"), ""]
    stuck = [r for r in rows if r["stuck"]]
    changed = [r for r in rows if r["changed_this_week"]]
    out.append(f"{len(rows)} projects · {len(changed)} changed in the last {days} days · "
               f"{len(stuck)} look stuck · {len(late)} overdue todos")
    out.append("")

    out.append(h("Needs attention"))
    if not stuck:
        out.append("Nothing looks stuck.")
    for r in stuck:
        why = []
        if r["status"] == "blocked": why.append("status is blocked")
        if r["overdue"]: why.append(f"{r['overdue']} overdue")
        if not r["changed_this_week"] and r["open"]: why.append(f"no update in {days}+ days with {r['open']} open")
        out.append(f"- {STATUS_ICON.get(r['status'], '')} {b}{r['title']}{b} — {', '.join(why)}")
    out.append("")

    out.append(h("Overdue todos"))
    if not late:
        out.append("None.")
    for t in sorted(late, key=lambda t: t["by"]):
        due = datetime.fromtimestamp(int(t["by"]) / 1000, tz=timezone.utc).date().isoformat()
        out.append(f"- {t['task']} ({t.get('who') or 'unassigned'}, due {due}) — {t['project_title']}")
    out.append("")

    out.append(h("All projects"))
    for r in sorted(rows, key=lambda r: (r["status"] != "blocked", -(r["updated_at"].timestamp() if r["updated_at"] else 0))):
        upd = r["updated_at"].date().isoformat() if r["updated_at"] else "?"
        flag = " 🆕" if r["changed_this_week"] else ""
        out.append(f"- {STATUS_ICON.get(r['status'], '')} {b}{r['title']}{b} [{r['status']}] — "
                   f"{r['open']} open / {r['done']} done, updated {upd}{flag}")
    return "\n".join(out)


if __name__ == "__main__":
    print(build(slack="--slack" in sys.argv))
