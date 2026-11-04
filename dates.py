"""Natural-language due dates -> epoch ms, for Andy's shim and Dan's MCP server.

Why: Andy's Zap passes through whatever the Slack message said ("by Friday"), and Dan
types "tomorrow" at an LLM. Making every caller resolve that to an ISO date first was the
previous design (see add_todo's old docstring) and it leaked the API's calendar into the
prompt. `parse_due` does it once, here.

Rules, in order:
  1. empty / None                 -> None
  2. int/float, or an all-digit string that looks like epoch ms -> used verbatim
  3. ISO date or datetime         -> fast path through projects_client.to_ms
  4. a bare weekday ("Friday", "next fri", "on Thursday") -> the NEXT such weekday,
     never today and never the past (dateparser returns *today* for "Friday" on a
     Friday even with PREFER_DATES_FROM='future', which is wrong for a due date)
  5. "end of month" / "end of week" -> dateparser 1.4.3 returns None for these, so
     they are computed here (last day of this month / this coming Sunday)
  6. anything else                -> dateparser, future-biased, relative to now UTC
  7. unparseable                  -> None (callers turn that into a 400 / ValueError)

Normalisation: a resolved *date* becomes midnight UTC of that date. The API stores
whatever we send (API_NOTES.md: `by` is verbatim), so pinning every date-only answer to
00:00Z keeps the overdue comparison consistent across surfaces. An explicit time
("Friday 5pm", an ISO datetime) is kept, since the caller meant it, and an epoch-ms int
is passed through untouched.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import dateparser

from projects_client import to_ms

_WEEKDAYS = {"mon": 0, "tue": 1, "tues": 1, "wed": 2, "wednes": 2, "thu": 3, "thur": 3,
             "thurs": 3, "fri": 4, "sat": 5, "satur": 5, "sun": 6}

# "Friday", "fri.", "next Friday", "on thursday", "this coming Tuesday"
_WEEKDAY_RE = re.compile(
    r"^(?:by\s+|on\s+|due\s+)?(?:this\s+|next\s+|the\s+|coming\s+)*"
    r"(mon|tues?|wednes|wed|thurs?|thu|fri|satur|sat|sun)(?:day)?\.?$",
    re.IGNORECASE,
)

# dateparser 1.4.3 parses neither of these, and both are things a Slack message says.
_EOM_RE = re.compile(r"^(?:by\s+|due\s+)?(?:the\s+)?(?:end\s+of\s+(?:the\s+)?(month|week)|eom|eow)\.?$",
                     re.IGNORECASE)

_SETTINGS = {
    "PREFER_DATES_FROM": "future",
    "RETURN_AS_TIMEZONE_AWARE": True,
    "TIMEZONE": "UTC",
    "TO_TIMEZONE": "UTC",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _midnight_ms(d: datetime) -> int:
    return to_ms(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))


def _next_weekday(target: int, base: datetime) -> int:
    """Strictly-future occurrence of `target` (0=Mon). Today never counts."""
    ahead = (target - base.weekday()) % 7 or 7
    return _midnight_ms(base + timedelta(days=ahead))


def parse_due(text) -> int | None:
    """Due-date text -> epoch ms, or None if empty/unparseable. See module docstring."""
    if text is None:
        return None
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return int(text)
    if isinstance(text, datetime):
        return to_ms(text)

    s = str(text).strip()
    if not s:
        return None

    # epoch ms straight from a machine (a 13-digit number); a short digit run is a year etc.
    if re.fullmatch(r"-?\d{11,}", s):
        return int(s)

    # ISO fast path - no need to wake dateparser for "2026-11-07" / "2026-11-07T09:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        pass
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return to_ms(dt) if (dt.hour or dt.minute or dt.second) else _midnight_ms(dt)

    base = _now()

    m = _EOM_RE.match(s)
    if m:
        unit = (m.group(1) or ("month" if s.lower().rstrip(".").endswith("eom") else "week")).lower()
        if unit == "month":
            nxt = (base.replace(day=1) + timedelta(days=31)).replace(day=1)
            return _midnight_ms(nxt - timedelta(days=1))
        return _next_weekday(6, base)  # end of week = this coming Sunday

    m = _WEEKDAY_RE.match(s)
    if m:
        return _next_weekday(_WEEKDAYS[m.group(1).lower()], base)

    dt = dateparser.parse(s, settings={**_SETTINGS, "RELATIVE_BASE": base.replace(tzinfo=None)})
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # dateparser hands back the current clock time for date-only input; treat a result
    # within a second of the relative base as "no time was given" and pin it to midnight.
    if abs((dt - base).total_seconds()) % 86400 < 2 or (dt.hour, dt.minute) == (base.hour, base.minute):
        return _midnight_ms(dt)
    return to_ms(dt)


if __name__ == "__main__":
    for s in ("Friday", "next Friday", "tomorrow", "in 3 days", "end of month",
              "Nov 7", "2026-11-07", "2026-11-07T09:30", "", "garbage", 1762000000000):
        ms = parse_due(s)
        print(f"{s!r:24} -> {ms} {datetime.fromtimestamp(ms/1000, timezone.utc).isoformat() if ms else ''}")
