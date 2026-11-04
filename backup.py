"""Dump every project and todo to JSON. The API is in memory and resets on restart; this makes that a non-event.

    .venv/bin/python backup.py                 # -> backups/<UTC timestamp>.json
    .venv/bin/python backup.py latest.json     # -> that path
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from projects_client import Projects

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backups") / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    projects = Projects().list_projects()
    out.write_text(json.dumps({"taken_at": datetime.now(timezone.utc).isoformat(), "projects": projects}, indent=1))
    print(f"{len(projects)} projects, {sum(len(p.get('items') or []) for p in projects)} todos -> {out}")
