# Findings: write (round 1)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 40 of 40

## POST /api/v1/proj/new

### Attempt 1
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: none
Body: none
Response: HTTP 400
```
{"error":"title is required"}
```
Note: no other fields were checked yet — only `title` is reported missing.

### Attempt 2
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"write-probe-1"}
Response: HTTP 201
```
{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}
```
Note: id format is `proj_` + 6 lowercase hex chars; default status is `kickoff`; `updated_at` is Unix epoch milliseconds (1793578023313 = 2026-11-01); `description` defaults to `""`; `items` defaults to `[]`.

### Attempt 3 (wrong type)
Request: POST .../api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":12345}
Response: HTTP 201
```
{"description":"","id":"proj_7e9c14","items":[],"status":"kickoff","title":12345,"updated_at":1793578044120}
```
Note: no type coercion/validation on `title` — a JSON number is stored and echoed back as-is.

### Attempt 4 (trailing slash)
Request: POST .../api/v1/proj/new/
Headers: Content-Type: application/json
Body: {"title":"write-probe-trailing"}
Response: HTTP 404
```
{"error":"not found"}
```
Note: trailing slash is not normalized — this is a distinct, non-matching route. No project created.

### Attempt 5 (enum case variant: lowercase "active" — not in the accepted set)
Request: POST .../api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"write-probe-status-active","status":"active"}
Response: HTTP 400
```
{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}
```
Note: this response revealed the full enum of valid `status` values.

### Attempt 6 (enum case variant: "Active")
Request: POST .../api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"write-probe-status-Active","status":"Active"}
Response: HTTP 400
```
{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}
```

### Attempt 7 (valid enum value, lowercase: "wip")
Request: POST .../api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"write-probe-status-wip","status":"wip"}
Response: HTTP 201
```
{"description":"","id":"proj_a1b7b3","items":[],"status":"wip","title":"write-probe-status-wip","updated_at":1793578058911}
```
Note: `status` can be set on create, overriding the `kickoff` default.

### Attempt 8 (enum case variant: "WIP", uppercase of a valid value)
Request: POST .../api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"write-probe-status-WIP","status":"WIP"}
Response: HTTP 400
```
{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}
```
Note: enum matching is case-sensitive; only the exact lowercase strings are accepted.

## PUT /api/v1/proj/modify

### Attempt 1
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/modify
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 2
Request: PUT .../api/v1/proj/modify
Headers: Content-Type: application/json
Body: {"id":"proj_aa6cb4","title":"write-probe-1-modified"}
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: identical 405 with or without a body — PUT is rejected at the routing layer before any body is read.

### Attempt 3 (discover allowed methods)
Request: OPTIONS .../api/v1/proj/modify
Headers: none
Body: none
Response: HTTP 200
```
allow: GET, HEAD, OPTIONS
(no response body)
```
Note: the server itself reports that only GET, HEAD, OPTIONS are allowed on this path — PUT was never going to work.

### Attempt 4 (try POST instead of PUT)
Request: POST .../api/v1/proj/modify
Headers: Content-Type: application/json
Body: {"id":"proj_aa6cb4","title":"write-probe-1-modified"}
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 5 (try GET, no params)
Request: GET .../api/v1/proj/modify
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: unlike `/new`'s "title is required", this is a lookup-style error, implying the handler tries to resolve a project id even with zero params.

### Attempt 6 (GET with id+title as query string, id of a project that DOES exist)
Request: GET .../api/v1/proj/modify?id=proj_aa6cb4&title=write-probe-1-modified
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: `proj_aa6cb4` exists (confirmed by a later verification read) but is still reported as not found.

### Attempt 7 (field name candidate: project_id)
Request: GET .../api/v1/proj/modify?project_id=proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 8 (field name candidate: pid)
Request: GET .../api/v1/proj/modify?pid=proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 9 (id as path segment instead of query string)
Request: GET .../api/v1/proj/modify/proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: different error string than the query-string attempts ("not found" vs "no such project") — this is a routing 404 (no such route), not a lookup failure.

### Attempt 10 (garbage/nonexistent id, same query shape as attempt 6, to isolate cause)
Request: GET .../api/v1/proj/modify?id=garbage_nonexistent
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: identical response for a real id and a garbage id — the `id` query param appears to have no effect on this handler's outcome; GET on this path always returns "no such project".

### Attempt 11 (try PATCH, for completeness against the OPTIONS Allow header)
Request: PATCH .../api/v1/proj/modify
Headers: Content-Type: application/json
Body: {"id":"proj_aa6cb4","title":"x"}
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 12 (GET with a JSON body instead of query string)
Request: GET .../api/v1/proj/modify
Headers: Content-Type: application/json
Body: {"id":"proj_aa6cb4","title":"write-probe-1-modified"}
Response: connection error, no HTTP status
```
curl exit code 92 (HTTP/2 stream error), HTTP 000, no body returned
```
Note: inconclusive — likely an HTTP/2 client-level rejection of a body on GET, not an API-level signal. Not treated as a finding about the API.

### Attempt 13 (trailing slash)
Request: GET .../api/v1/proj/modify/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

## POST /api/v1/proj/touch

### Attempt 1
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/touch
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 2 (discover allowed methods)
Request: OPTIONS .../api/v1/proj/touch
Headers: none
Body: none
Response: HTTP 200
```
allow: GET, HEAD, OPTIONS
(no response body)
```
Note: same pattern as `/modify` — POST is categorically rejected by routing.

### Attempt 3 (GET, no params)
Request: GET .../api/v1/proj/touch
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 4 (GET with id of a real, existing project as query string)
Request: GET .../api/v1/proj/touch?id=proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: identical to attempt 3 (no params) — same behavior as `/modify`: the query string appears to have no effect.

### Attempt 5 (id as path segment)
Request: GET .../api/v1/proj/touch/proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 6 (trailing slash)
Request: GET .../api/v1/proj/touch/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

Note: because no shape ever got past "no such project" / "method not allowed", I could not reach the state-changing behavior of `touch` at all — the before/after `updated_at` comparison in the priorities could not be performed. See "Could not determine".

## DELETE /api/v1/proj/remove (fixture, cleanup)

### Attempt 1 (fixture)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 2 (fixture)
Request: DELETE .../api/v1/proj/remove
Headers: Content-Type: application/json
Body: {"id":"proj_aa6cb4"}
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 3 (fixture, discover allowed methods)
Request: OPTIONS .../api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 200
```
allow: GET, HEAD, OPTIONS
(no response body)
```

### Attempt 4 (fixture, GET with id query string)
Request: GET .../api/v1/proj/remove?id=proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 5 (fixture, field name candidate: projectId)
Request: GET .../api/v1/proj/remove?projectId=proj_aa6cb4
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 6 (fixture, REST-style DELETE directly on the resource path)
Request: DELETE .../api/v1/proj/proj_aa6cb4
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 7 (fixture, OPTIONS on the resource path)
Request: OPTIONS .../api/v1/proj/proj_aa6cb4
Headers: none
Body: none
Response: HTTP 200
```
allow: GET, HEAD, OPTIONS
(no response body)
```
Note: same Allow set as `/modify`, `/touch`, `/remove` — no path in this API advertises POST/PUT/DELETE/PATCH as allowed, anywhere I probed.

## GET /api/v1/proj (verification read)

### Attempt 1 (verification read, default page)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{"description":"Public launch of v3. Coordinate marketing, eng, and CS.","id":"proj_23315f","items":[{"by":1793750085470,"done":false,"id":"todo_9e5e55","task":"Finalize launch blog post","who":"betty"},{"by":1793922885470,"done":false,"id":"todo_76344a","task":"QA the onboarding flow on staging","who":"carlos"},{"by":1793836485470,"done":true,"id":"todo_68ddc7","task":"Draft launch-day Slack post","who":"andy"},{"by":1794095685470,"done":false,"id":"todo_a5c40c","task":"Update the help center landing page","who":"dan"}],"status":"wip","title":"Spring product launch","updated_at":1793577285470},
... [truncated, response contains 5 projects total, see attempt 2/3 for the remainder] ...
],"take":5,"total":13}
```
Note: these 5 projects (titles "Spring product launch", "Enterprise pilot, Acme Co.", "Migrate billing to new processor", "Internal AI tooling rollout", "Q2 brand refresh") were already present before I created anything — I did not create and must not touch them.

### Attempt 2 (verification read, ?take=20)
Request: GET .../api/v1/proj?take=20
Headers: none
Body: none
Response: HTTP 200
```
(identical to attempt 1: "from":0, same 5 projects, "take":5, "total":13)
```
Note: the `take` query parameter has no effect — page size is fixed at 5 regardless of what is requested.

### Attempt 3 (verification read, ?from=5, to find my own created projects)
Request: GET .../api/v1/proj?from=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":5,"projects":[{"description":"Reduce time-to-first-value from 7 days to 2.","id":"proj_828748", ... "title":"Customer onboarding redesign", ...},{"description":"Move from manual schedule to PagerDuty.","id":"proj_bd0d1e", ... "title":"On-call rotation revamp", ...},{"description":"","id":"proj_dc0698","items":[],"status":"kickoff","title":"items-fixture-1","updated_at":1793578016712},{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876},{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}],"take":5,"total":13}
```
Note: `from` paginates correctly. This confirms `proj_aa6cb4` ("write-probe-1") exists server-side with exactly the fields returned at creation — which makes the repeated "no such project" from `/modify` and `/touch` on this same id even more notable. Also visible: `items-fixture-1` (proj_dc0698) and `remove-fixture-1` (proj_8e63a5) — fixtures from other slices' probers, not created by me, left untouched.

### Attempt 4 (verification read, ?from=5, final check before writing up)
Request: GET .../api/v1/proj?from=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":5,"projects":[{"description":"Reduce time-to-first-value from 7 days to 2.","id":"proj_828748", ... "title":"Customer onboarding redesign", ...},{"description":"Move from manual schedule to PagerDuty.","id":"proj_bd0d1e", ... "title":"On-call rotation revamp", ...},{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876},{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313},{"description":"","id":"proj_24200b","items":[],"status":"kickoff","title":"remove-fixture-2","updated_at":1793578024905}],"take":5,"total":12}
```
Note: `total` dropped from 13 to 12 between attempt 3 and attempt 4 — `items-fixture-1` (proj_dc0698) disappeared, meaning some other prober (likely the "remove" or "items" slice) successfully deleted a project through a mechanism I never found. A new project `remove-fixture-2` (proj_24200b) also appeared, created by another slice's prober. Both are outside my slice; left untouched.

## GET /api/v1/proj/<id> (verification read, outside slice)

### Attempt 1
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_aa6cb4
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}
```
Note: single-project GET by id (plain `/api/v1/proj/<id>`) works and returns 200 — only the `modify`/`touch`/`remove` sub-paths are broken for this id.

## Could not determine
- How `PUT /api/v1/proj/modify` is actually meant to be invoked: OPTIONS reports only GET, HEAD, OPTIONS as allowed on this exact path, and GET always returns `{"error":"no such project"}` regardless of params (query string with `id`/`project_id`/`pid`, path segment, no params, or a real vs. garbage id all gave the identical response). Next to try: check whether a request header (API key, auth token, a specific `Accept` or custom header) changes this behavior, or whether the real mutate route lives at a different path entirely (e.g. ask the "proj" read-slice prober or check for a path like `/api/v1/proj/<id>` with a non-GET verb that I have not yet discovered — I tried DELETE and it 405'd, but PUT/PATCH on `/api/v1/proj/<id>` were not tried).
- Same open question for `POST /api/v1/proj/touch`: identical symptom (OPTIONS → GET/HEAD/OPTIONS only; GET always 404 "no such project" regardless of id). Could not observe any `updated_at` change, so the before/after comparison the dispatch asked for was never performed.
- Whether `status` can be changed via some other verb/shape I haven't found, and if so, whether the same case-sensitive enum (`blocked`, `dropped`, `kickoff`, `wip`, `wrapped`) applies to updates as it does to creation.
- Whether `description` can be set on create (only `title` and `status` were tried as create-time fields; `description` was never explicitly sent on `/new`).
- How another, unidentified prober successfully deleted `items-fixture-1` (proj_dc0698) between my verification reads — try asking what path/method/body it used, since it clearly found a working route for project deletion that I did not.
- Exact trailing-slash/path-segment behavior for `/api/v1/proj/new` combined with a valid body was tested (404, route not found) but the same was not tested for `/modify` or `/touch` with a body attached (only did it with no params) — low priority since the 405/404 pattern was already consistent across all variations tried.

## Cleanup
- write-probe-1 (proj_aa6cb4) → DELETE via `/api/v1/proj/remove` (DELETE method) → HTTP 405 (method not allowed); DELETE via `/api/v1/proj/proj_aa6cb4` → HTTP 405; GET `/api/v1/proj/remove?id=proj_aa6cb4` → HTTP 404 "no such project". **Cleanup FAILED — project still exists.**
- write-probe-status-wip (proj_a1b7b3) → never attempted a dedicated delete call (ran out of budget); same remove mechanism that failed for proj_aa6cb4 would apply. **Cleanup NOT ATTEMPTED — project still exists.**
- title=12345 (proj_7e9c14, numeric title from the wrong-type test) → never attempted a dedicated delete call (ran out of budget). **Cleanup NOT ATTEMPTED — project still exists.**

All three projects I created remain on the server. I could not find any working method/path/param combination to delete a project within my 40-call budget. This should be flagged to whoever owns the `remove` slice or has found a working delete path, and/or retried in round 2 with different field names or headers.
