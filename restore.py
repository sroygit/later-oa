"""Replay a backup (or a hand-written seed) into the API after a reset.

    .venv/bin/python restore.py backups/<file>.json [--dry-run] [--force]

Ids are server-generated, so they come back different; titles, descriptions, statuses, todos, assignees,
due dates and done flags are restored. Projects whose title already exists are skipped unless --force.
Input shape is what backup.py writes, or just {"projects": [{"title", "description", "status", "items": [{"task","who","by","done"}]}]}.
"""
from __future__ import annotations

import json
import sys

from projects_client import Projects


def restore(path: str, dry_run: bool = False, force: bool = False) -> None:
    data = json.load(open(path))
    projects = data["projects"] if isinstance(data, dict) else data
    api = Projects()
    existing = {str(p.get("title", "")).lower() for p in api.list_projects()}
    for p in projects:
        title = str(p.get("title", ""))
        items = p.get("items") or []
        if title.lower() in existing and not force:
            print(f"skip   {title!r} (exists)")
            continue
        print(f"create {title!r} [{p.get('status', 'kickoff')}] with {len(items)} todos")
        if dry_run:
            continue
        new = api.create(title, p.get("description") or "", p.get("status") or "kickoff")
        for t in items:
            made = api.add_item(new["id"], str(t.get("task", "")), who=str(t.get("who") or ""), by=t.get("by"), touch=False)
            if t.get("done"):
                api.mark(new["id"], made["id"], True, touch=False)
        api.touch(new["id"])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    restore(args[0], dry_run="--dry-run" in sys.argv, force="--force" in sys.argv)
