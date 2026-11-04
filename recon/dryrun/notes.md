# Projects API notes (after round 0)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Generated from: recon/dryrun/health.md

## Confirmed behaviour

### GET /api/v1/health
- Purpose: liveness check; no auth, no input.
- Accepts: nothing. Headers: none required. Extra query params (e.g. `?id=1`) are silently ignored. [health.md#Attempt 1] [health.md#Attempt 3]
- Returns: HTTP 200 with `{"status":"ok"}` [health.md#Attempt 1] [health.md#Attempt 3]
- Errors seen: HTTP 404 `{"error":"not found"}` when the path has a trailing slash (`/api/v1/health/`) [health.md#Attempt 2]

### Identifiers and formats
- Project id: not observed
- Todo id: not observed
- Dates: not observed
- Status values seen: not observed (the `status` field in the health body is a liveness string `"ok"`, not a project/todo status) [health.md#Attempt 1]
- Error body shape: `{"error":"<message>"}` [health.md#Attempt 2]

## Quirks
- Trailing slash changes behaviour: `/api/v1/health/` is HTTP 404, `/api/v1/health` is HTTP 200. Paths are matched exactly; clients must not append `/`. [health.md#Attempt 2]

## Unresolved
- Try POST /api/v1/health with no body. Record the status code (405 vs 404 vs 200) and whether the body is `{"error":"..."}`.
- Try PUT /api/v1/health with no body. Record the status code and body.
- Try DELETE /api/v1/health with no body. Record the status code and body.
