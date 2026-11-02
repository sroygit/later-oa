# Decisions

Clock: started 2026-11-02T00:05:22Z. Everything below was done inside the 90 minutes except the agent prompt files, which were written beforehand with no API calls (see `recon/RUNLOG.md` for the timeline).

## The one design argument

One thin client, four surfaces. `projects_client.py` absorbs every quirk (path-segment ids, page size 5, epoch-ms dates, `"yes"/"no"` flags, case-sensitive enum) so Dan's MCP server, Carlos's digest, Betty's UI, and Andy's shim are each under 120 lines and share the same `summary()`, `overdue()`, and `find_project()` helpers. Fix a quirk once, every persona benefits.

## What I built, in leverage order

1. **Recon as a two-tier agent system** (not a person with curl). Four cheap probers in parallel, one expensive synthesizer, one expensive reviewer that rewrites the probers' prompt from their failures, then a narrow second round. `API_NOTES.md` is a deliverable: it is the documentation the brief said doesn't exist, with a citation to raw evidence for every claim.
2. **Dan: MCP server.** Highest leverage. Nine tools, name-based resolution so "the launch project" works, due dates as ISO strings so the LLM does the "Friday" math. Registered in `.mcp.json`; Claude Code picks it up in this folder. Also gives Carlos a `portfolio_summary` tool for free.
3. **Carlos: one-command digest.** `digest.py` prints markdown or Slack mrkdwn. "Stuck" = blocked, or has overdue todos, or no update in 7 days with open todos. "Changed this week" = `updated_at` within 7 days. Cron line in the docstring; I did not build a scheduler or a Slack poster.
4. **Andy: webhook shim** rather than "call the API directly". The API wants ids in the path and a literal `"yes"` flag; a Zap would need two lookups first and the list only pages 5 at a time. The shim takes names in query, form, or JSON. `ZAPIER.md` has the exact step config.
5. **Betty: Streamlit.** Last because it's the least leveraged and the most time-hungry. It covers create, status change, add/complete/delete todo, and a portfolio tab. Hand-off is `streamlit run app.py`.

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
- **Only `touch` moves `updated_at`.** Modify, add, mark, and yank all leave it frozen at creation time (round two, verified by the client's own test). So `updated_at` is not "last changed", it is "last touched". The client touches after every mutation, which makes Carlos's "changed this week" and "stuck" honest for anything that goes through this client. Changes made by raw curl stay invisible, and that's documented, not hidden.
- Todo lookups are scoped to the project in the path: a todo id from project A via project B's path is a 404, so the shim's name resolution can't cross-wire projects.

## What I'd do with a full day

- **Fix the recon prompt before the probers run, not after.** The reviewer's rewrite correctly says "sweep path shapes before field names"; with a day I'd run a third round and measure whether the rewritten prompt actually finds nested routes faster on a fresh API.
- **Collapse the MCP server and the webhook shim** into one FastAPI app exposing both HTTP and MCP (fastmcp can mount on Starlette). One process for Andy and Dan.
- **Carlos's "stuck" signal shouldn't depend on `updated_at` at all.** Round two showed it only moves on `touch`, so anyone writing to the API without this client leaves no trace. With a day I'd have the digest snapshot the full project list to SQLite on each run and compute "changed this week" by diffing snapshots, which works no matter who wrote.
- **Betty's UI should be a single HTML file**, not Streamlit, so it can be emailed. Streamlit was faster to write, not better to hand off.
- **Natural-language dates in the shim** ("Friday") so Andy's Zap can pass through whatever the Slack message said.
