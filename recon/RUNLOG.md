# Recon run log

One line per agent run, appended by the agent itself. Orchestrator notes are prefixed `ORCH`.

Format:
`- <ISO-8601 time> | <agent> | <key=value ...> | outcome=<ok|partial|failed> | <one sentence>`

- 2026-11-01T23:54:58Z | prober | slice=dryrun round=0 calls=3 | outcome=ok | Confirmed GET /api/v1/health returns {"status":"ok"} with HTTP 200, ignores extra query params, and rejects a trailing slash with HTTP 404.
- 2026-11-01T23:56:03Z | ORCH | task=2 dispatch=fallback | outcome=ok | Agent tool did not find subagent_type prober (types load at session start); dispatched general-purpose with model=sonnet and the definition body inlined, as documented in RUNBOOK.md.
