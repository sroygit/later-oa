# Decisions

Clock: started 2026-11-02T00:05:22Z. Everything below was done inside the 90 minutes except the agent prompt files, which were written beforehand with no API calls (see `recon/RUNLOG.md` for the timeline).

## The one design argument

One thin client, four surfaces. `projects_client.py` absorbs every quirk (path-segment ids, page size 5, epoch-ms dates, `"yes"/"no"` flags, case-sensitive enum) so Dan's MCP server, Carlos's digest, Betty's UI, and Andy's shim are each under 120 lines and share the same `summary()`, `overdue()`, and `find_project()` helpers. Fix a quirk once, every persona benefits.

## What I built, in leverage order

1. **Recon as a two-tier agent system** (not a person with curl). Four cheap probers in parallel, one expensive synthesizer, one expensive reviewer that rewrites the probers' prompt from their failures, then a narrow second round. `API_NOTES.md` is a deliverable: it is the documentation the brief said doesn't exist, with a citation to raw evidence for every claim.

   How it went, by the numbers (`recon/RUNLOG.md`):

   | | Round 1 | Round 2 (rewritten prompt) |
   |---|---|---|
   | Probers | 4 | 3 |
   | curl calls | 134 | 75 |
   | Fixtures left undeleted | 5 | 0 |
   | Endpoints confirmed after synthesis | 10 of 12 | 12 of 12 |
   | Unresolved items after synthesis | 44 | 5 |

   The reviewer's diagnosis was right: three of four round-one probers burned their budget on the brief's flat paths, because the prompt said "sweep field names" before "try the nested path". Its rewrite put path shape first and capped flat-path attempts at three. Round two probers hit the real routes on their first call every time. Clock cost of the whole agent phase: about 20 minutes, of which I spent maybe 4 reading outputs. The rest of the time I was building the client and the surfaces in parallel.
2. **Dan: MCP server.** Highest leverage. Nine tools, name-based resolution so "the launch project" works. Registered in `.mcp.json`; Claude Code picks it up in this folder. Also gives Carlos a `portfolio_summary` tool for free.
3. **Carlos: one-command digest, with its own change history.** `digest.py` prints markdown or Slack mrkdwn (`--slack`, `--days N`). It does not trust `updated_at`: round two proved only `touch` moves it, so anyone writing to the API without this client leaves no trace there. Instead `snapshots.py` stores the full project list (items embedded) to `snapshots.sqlite` on every run and `diff()` compares the newest snapshot with the oldest one inside the window, producing named change items — projects created/removed/renamed/status/description, todos added/completed/reopened/removed/reassigned/due-date — grouped by project under "What changed this week". That works no matter who wrote. "Changed this week" per project is now "has diff items"; "stuck" = blocked, or an overdue open todo, or no diff items in the window with open todos (terminal statuses `wrapped`/`dropped` are exempt, so a finished project is not nagged about). `updated_at` survives only as the first-run fallback, and the digest says "first run, using `updated_at`" on that run. Snapshots carry an epoch: if a new snapshot shares no project ids with the previous one, or the project count drops below the 7 seed projects, the shared take-home API has been reset, so the epoch increments and the differ never compares across it. Cron line in the docstring; I did not build a scheduler or a Slack poster.
4. **Andy: webhook shim** rather than "call the API directly". The API wants ids in the path and a literal `"yes"` flag; a Zap would need two lookups first and the list only pages 5 at a time. The shim takes names in query, form, or JSON. `ZAPIER.md` has the exact step config.

   **One process for all three.** `mcp_server.py` stays the module that defines the tools, and `webhook.py` imports `mcp` from it and mounts `mcp.http_app(path="/mcp")` (adopting its lifespan, which the streamable-http transport requires). So `uvicorn webhook:app --port 8787` serves Betty's page at `/`, Andy's routes, and Dan's nine tools at `/mcp` — one thing to start, one thing to tunnel through ngrok. Both transports stay available: `.mcp.json` still registers stdio, which is the entry the user has actually used in Claude Code, and the HTTP alternative (`claude mcp add --transport http later-projects-http http://localhost:8787/mcp`) is documented in the README rather than swapped in. Collapsing them was on the full-day list; it took ten lines, so it got done.

5. **Natural-language due dates** (`dates.py`, `parse_due`). Previously the MCP tool's docstring told the LLM to resolve "Friday" itself and Andy had to format an ISO date in his Zap. Now one function takes ISO, epoch ms, or English ("Friday", "tomorrow", "in 3 days", "end of month", "Nov 7") and both surfaces call it — the shim turns unparseable non-empty text into `400 could not parse due date: '<text>'`, the MCP tool raises `ValueError`, so Andy's Zap fails loudly instead of writing a wrong date. Two deliberate deviations from `dateparser`'s defaults: a bare weekday resolves to the **next** occurrence (dateparser returns *today* for "Friday" on a Friday even with `PREFER_DATES_FROM='future'`, which is never what a due date means), and "end of month"/"end of week" are computed here because dateparser 1.4.3 returns `None` for both. Every date-only answer is pinned to midnight UTC: the API stores `by` verbatim, so without that the overdue comparison would depend on what time of day the todo was created.
6. **Betty: Streamlit.** Last because it's the least leveraged and the most time-hungry. It covers create, status change, add/complete/delete todo, and a portfolio tab. Hand-off is `streamlit run app.py`.
   Then replaced by `betty.html`: one file, no external requests, served by the shim because the API has no CORS. Ticks, adds, deletes and status changes apply optimistically with a per-change rollback that surfaces the API's own error; only creating a project and the Refresh button re-fetch the list. A "no such project" on any write is treated as an API reset: the page reloads the list, re-selects the same project by title, and says so (added after the clock stop, after Later restarted the API mid-session and the page's ids went stale).

7. **The in-memory reset: not fought, made a non-event.** The client dumps everything to `backups/latest.json` after every write (one list walk, cheap at this scale, and a failed backup never fails the write); `backup.py` does the same on demand; `restore.py` replays it (projects, todos, assignees, due dates, done flags) into a fresh API: missing projects are created, existing ones get a todo-level merge by task text, and it re-reads the API afterwards and reports anything still missing. (Merge and verify were added after the clock stop; see the run log.) Ids come back different, which is fine because every surface here resolves by name. The digest's snapshot store is a second, automatic backup.

## What I skipped and why

- **Auth, tests, observability.** Not graded, said so in the brief.
- **A real scheduler or Slack integration for Carlos.** A cron line and a webhook poster are ten minutes of glue with no decisions in them.
- **Exposing the shim publicly.** `ngrok http 8787` is in the doc; it's not a design choice.
- **Pagination and form-body edge cases in round two.** The client walks pages and sends JSON, so the answers wouldn't change any code.
- **Making the agent system reusable across tasks.** Deliberately one loop, two rounds. "Self-improving" here means one honest iteration: the reviewer's rewrite is in `recon/PROMPT_CHANGELOG.md` and the git diff.

## Quirks that bit (full list in API_NOTES.md)

- Every mutating path in the brief is wrong. Ids are path segments; the flat paths fall through to the single-project GET with the verb as the id, so you get 405 "method not allowed" which reads as "wrong verb" when it means "wrong path". Three of four probers burned their whole budget on this.
- `OPTIONS` Allow headers only describe the exact path, so they can't discover sub-routes.
- `take` is clamped to 5 and the response echoes the clamped value.
- `by` (due date) accepts any JSON value verbatim; a string date is stored as a string. The client always sends epoch ms and tolerates strings on read.
- `mark` takes `flag: "yes"|"no"`, not a boolean, and sets rather than toggles.
- **Only `touch` moves `updated_at`.** Modify, add, mark, and yank all leave it frozen at creation time (round two, verified by the client's own test). So `updated_at` is not "last changed", it is "last touched". The client touches after every mutation, which makes Carlos's "changed this week" and "stuck" honest for anything that goes through this client. Changes made by raw curl are invisible to `updated_at`, which is why the digest now derives change from its own snapshots (`snapshots.py`) instead; `updated_at` is only the first-run fallback.
- A todo created without a due date gets `by` = request time, not null. So "no due date" is indistinguishable from "due now", and such a todo shows as overdue tomorrow. Neither the client nor the UI invents a sentinel; the digest and the UI show what the API stores. Fix on the API side is the right fix.
- Todo lookups are scoped to the project in the path: a todo id from project A via project B's path is a 404, so the shim's name resolution can't cross-wire projects.

## What I'd do with a full day

- **A contract check derived from `API_NOTES.md`.** Every confirmed claim (nested route shapes, the status enum and its case sensitivity, the yes/no flag, the page cap of 5, the three distinct 404/405 messages, only touch moving `updated_at`) as a pass/fail assertion against the live API, one fixture, a few seconds. Run it before every demo and on the digest's cron, and only re-run the probers when it goes red. Today the only way to ask "did the API change" is to re-dispatch the probers, which is slow and gives prose, not a verdict.
- **Fix the recon prompt before the probers run, not after.** The reviewer's rewrite correctly says "sweep path shapes before field names"; with a day I'd run a third round and measure whether the rewritten prompt actually finds nested routes faster on a fresh API.
- **A timezone for natural-language dates.** `parse_due` is UTC-only. Andy's Slack message saying "Friday" means Friday in Andy's timezone, and the API has no notion of one; a day would buy a per-caller `tz` and an honest answer about what midnight means.
