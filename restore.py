"""Replay a backup (or a hand-written seed) into the API after a reset.

    .venv/bin/python restore.py backups/<file>.json [--dry-run] [--force]

What it does, in order:
  1. loads the file fully (the client's autobackup may overwrite backups/latest.json mid-restore)
  2. reads the current API state once
  3. for each project in the file:
       - title missing from the API  -> create it with every todo, mark the done ones, touch once
       - title already present       -> todo-level merge: add any todo whose task text is missing,
                                        and mark done any todo the file says is done but the API says isn't
  4. re-reads the API and reports anything from the file that is still missing

Ids are server-generated, so they come back different; --force recreates projects even when the
title exists (duplicates), only useful against an empty API. --dry-run prints the plan and writes nothing.
"""
from __future__ import annotations

import json
import sys

from projects_client import Projects


def _key(s) -> str:
    return str(s or "").strip().lower()


def _load(path: str) -> list[dict]:
    data = json.load(open(path))
    return data["projects"] if isinstance(data, dict) else data


def restore(path: str, dry_run: bool = False, force: bool = False) -> int:
    wanted = _load(path)
    api = Projects()
    current = {_key(p.get("title")): p for p in api.list_projects()}
    created = merged = added = marked = 0

    for p in wanted:
        title = str(p.get("title", ""))
        items = p.get("items") or []
        live = current.get(_key(title))

        if live is None or force:
            created += 1
            print(f"create {title!r} [{p.get('status', 'kickoff')}] with {len(items)} todos")
            if dry_run:
                continue
            new = api.create(title, p.get("description") or "", p.get("status") or "kickoff")
            for t in items:
                made = api.add_item(new["id"], str(t.get("task", "")), who=str(t.get("who") or ""), by=t.get("by"), touch=False)
                if t.get("done"):
                    api.mark(new["id"], made["id"], True, touch=False)
            api.touch(new["id"])
            continue

        # title exists: merge todos by task text
        live_items = {_key(t.get("task")): t for t in (live.get("items") or [])}
        missing = [t for t in items if _key(t.get("task")) not in live_items]
        undone = [live_items[_key(t.get("task"))] for t in items
                  if t.get("done") and _key(t.get("task")) in live_items and not live_items[_key(t.get("task"))].get("done")]
        if not missing and not undone:
            print(f"ok     {title!r} (all {len(items)} todos present)")
            continue
        merged += 1
        print(f"merge  {title!r}: add {len(missing)} missing todo(s), mark {len(undone)} done")
        for t in missing:
            print(f"         + {t.get('task')!r}")
        if dry_run:
            continue
        for t in missing:
            made = api.add_item(live["id"], str(t.get("task", "")), who=str(t.get("who") or ""), by=t.get("by"), touch=False)
            added += 1
            if t.get("done"):
                api.mark(live["id"], made["id"], True, touch=False)
        for t in undone:
            api.mark(live["id"], t["id"], True, touch=False)
            marked += 1
        api.touch(live["id"])

    print(f"\n{'planned' if dry_run else 'done'}: {created} created, {merged} merged ({added} todos added, {marked} marked done)")
    if dry_run:
        return 0

    # verify: everything in the file should now exist by title and task text
    after = {_key(p.get("title")): p for p in api.list_projects()}
    problems = 0
    for p in wanted:
        live = after.get(_key(p.get("title")))
        if live is None:
            problems += 1
            print(f"MISSING project {p.get('title')!r}")
            continue
        have = {_key(t.get("task")): t for t in (live.get("items") or [])}
        for t in p.get("items") or []:
            lt = have.get(_key(t.get("task")))
            if lt is None:
                problems += 1
                print(f"MISSING todo {t.get('task')!r} in {p.get('title')!r}")
            elif bool(t.get("done")) and not lt.get("done"):
                problems += 1
                print(f"NOT DONE todo {t.get('task')!r} in {p.get('title')!r}")
    print("verify: OK, API matches the file" if not problems else f"verify: {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    sys.exit(restore(args[0], dry_run="--dry-run" in sys.argv, force="--force" in sys.argv))
