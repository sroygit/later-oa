# Findings: remove (round 1)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 31 of 40

## POST /api/v1/proj/new (fixture)

### Attempt 1 (fixture)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"remove-fixture-1"}
Response: HTTP 201
```
{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876}
```
Note: Accepted immediately; id format is `proj_` + 6 hex chars; default status "kickoff".

### Attempt 2 (fixture)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"remove-fixture-2"}
Response: HTTP 201
```
{"description":"","id":"proj_24200b","items":[],"status":"kickoff","title":"remove-fixture-2","updated_at":1793578024905}
```
Note: Second fixture created so we could test deleting one existing id and then deleting it again.

## DELETE /api/v1/proj/remove

### Attempt 1
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: No parameters at all; DELETE verb itself is rejected before any body/params are considered.

### Attempt 2
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Checked whether the real verb for this path is POST instead of DELETE; still rejected.

### Attempt 3
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: Reveals that "/api/v1/proj/remove" is being matched by a generic GET /api/v1/proj/:id route, with "remove" treated as a literal (invalid) project id — not a dedicated removal route.

### Attempt 4
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 5
Request: PATCH https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 6
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: none
Body: none
Response: HTTP 200
```
(empty body)
```
Note: Response header `allow: GET, HEAD, OPTIONS` — DELETE/POST/PUT/PATCH are not in the allowed-methods list for this exact path, confirmed authoritatively (not just inferred from 405s).

### Attempt 7
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_8e63a5
Headers: none
Body: none
Response: HTTP 200
```
(empty body)
```
Note: Same `allow: GET, HEAD, OPTIONS` header for a real project id in this position — confirms /api/v1/proj/remove is handled by the generic /api/v1/proj/:id route (id="remove"), and that route never supports DELETE, regardless of what the id is.

### Attempt 8
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj
Headers: none
Body: none
Response: HTTP 200
```
(empty body)
```
Note: `allow: GET, HEAD, OPTIONS` — base /api/v1/proj also has no DELETE.

### Attempt 9
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: none
Body: none
Response: HTTP 200
```
(empty body)
```
Note: Comparison point — `allow: GET, POST, HEAD, OPTIONS`. /new is a distinct literal route (supports POST), unlike /remove which falls through to the generic :id route. This is strong evidence there is no working DELETE anywhere under /api/v1/proj for this slice's literal path.

### Attempt 10
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove/proj_8e63a5
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: Tried id as a third path segment (/remove/<id>) in case removal was path-based; this path pattern doesn't exist at all (generic 404, distinct from the "no such project" 404 seen for the :id route).

### Attempt 11
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove/proj_8e63a5
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: Same 3-segment path with DELETE verb — still generic 404, confirming this path shape has no route at all (not even a method restriction).

### Attempt 12
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_8e63a5
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: DELETE on an existing project id directly (no "/remove" segment) — also blocked at the method level.

### Attempt 13
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?id=proj_8e63a5
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Query-string id= on the literal /remove path; still 405.

### Attempt 14
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: X-HTTP-Method-Override: DELETE, Content-Type: application/json
Body: {"id":"proj_8e63a5"}
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Tried X-HTTP-Method-Override header as a long-shot; no effect.

### Attempt 15
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: Content-Type: application/json
Body: {"id":"proj_8e63a5"}
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: JSON body with id field; still blocked at method level before body is parsed.

### Attempt 16
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove
Headers: Content-Type: application/x-www-form-urlencoded
Body: id=proj_8e63a5
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 17 (trailing slash)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove/
Headers: Content-Type: application/json
Body: {"id":"proj_8e63a5"}
Response: HTTP 404
```
{"error":"not found"}
```
Note: Trailing slash changes the error from 405 ("method not allowed") to 404 ("not found") — the router treats the trailing-slash path as a different, non-existent route rather than normalizing it.

### Attempt 18 (id that does not exist)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?id=proj_doesnotexist
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Nonexistent id makes no difference — method check happens before any id lookup.

### Attempt 19 (wrong type: number instead of string)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?id=12345
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 20 (field name: project_id)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?project_id=proj_8e63a5
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 21 (field name: pid)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?pid=proj_8e63a5
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Stopped trying further field-name candidates (proj_id, projectId) once it was clear every DELETE call on this path returns the identical 405 "method not allowed" regardless of params — the OPTIONS Allow header (Attempt 6) already proves DELETE is not registered on this route at all, so no field name can succeed.

### Attempt 22 (cleanup attempt, remove-fixture-1)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?id=proj_8e63a5
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 23 (cleanup attempt, remove-fixture-2)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/remove?id=proj_24200b
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```

## GET /api/v1/proj (verification read)

### Attempt 1 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[... 5 projects, see below ...],"take":5,"total":11}
```
Note: List is paginated, default page size ("take") is 5, starting "from" 0; our 2 fixtures were not visible on this default page since they were appended at the end of the list (indexes 8 and 10).

### Attempt 2 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=20
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[... same 5 projects as Attempt 1 ...],"take":5,"total":11}
```
Note: `take` query param is ignored by the server — response still reports `"take":5` and still returns only 5 items. Pagination size appears fixed server-side.

### Attempt 3 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":5,"projects":[{"description":"Reduce time-to-first-value from 7 days to 2.","id":"proj_828748","items":[{"by":1793836485470,"done":false,"id":"todo_5d9f01","task":"Interview 5 recent signups","who":"carlos"},{"by":1794009285470,"done":false,"id":"todo_6bf0ca","task":"Audit current funnel drop-off","who":"betty"}],"status":"kickoff","title":"Customer onboarding redesign","updated_at":1793577285470},{"description":"Move from manual schedule to PagerDuty.","id":"proj_bd0d1e","items":[{"by":1790985285470,"done":false,"id":"todo_0fa167","task":"Get budget approval","who":"carlos"}],"status":"dropped","title":"On-call rotation revamp","updated_at":1793577285470},{"description":"","id":"proj_dc0698","items":[],"status":"kickoff","title":"items-fixture-1","updated_at":1793578016712},{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876},{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}],"take":5,"total":11}
```
Note: `from` query param works as a real pagination offset. Found remove-fixture-1 (proj_8e63a5) at index 8. Also observed other probers' fixtures (items-fixture-1, write-probe-1) — not touched, left alone per rule.

### Attempt 4 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=10
Headers: none
Body: none
Response: HTTP 200
```
{"from":10,"projects":[{"description":"","id":"proj_24200b","items":[],"status":"kickoff","title":"remove-fixture-2","updated_at":1793578024905},{"description":"","id":"proj_7e9c14","items":[],"status":"kickoff","title":12345,"updated_at":1793578044120}],"take":5,"total":12}
```
Note: Found remove-fixture-2 (proj_24200b) at index 10. Also saw a project (proj_7e9c14, not ours) with a numeric `title` (12345) instead of a string — presumably a different prober's edge-case test; not touched. `total` grew from 11 to 12 between calls because other probers were creating projects concurrently.

### Attempt 5 (verification read, post failed-cleanup check)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=8
Headers: none
Body: none
Response: HTTP 200
```
{"from":8,"projects":[{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876},{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313},{"description":"","id":"proj_24200b","items":[],"status":"kickoff","title":"remove-fixture-2","updated_at":1793578024905},{"description":"","id":"proj_7e9c14","items":[],"status":"kickoff","title":12345,"updated_at":1793578044120},{"description":"","id":"proj_a1b7b3","items":[],"status":"wip","title":"write-probe-status-wip","updated_at":1793578058911}],"take":5,"total":13}
```
Note: Both remove-fixture-1 (proj_8e63a5) and remove-fixture-2 (proj_24200b) are still present after every delete attempt — confirms cleanup did not succeed, consistent with DELETE being unsupported on this path.

## Could not determine
- Whether any HTTP method actually deletes a project anywhere in this API — every variation of DELETE (and POST/PUT/PATCH) on /api/v1/proj/remove, /api/v1/proj/<id>, and /api/v1/proj/remove/<id> returned 405 or 404; the OPTIONS Allow header for every path we could test only ever listed GET, HEAD, OPTIONS (plus POST for /api/v1/proj/new specifically). A real removal route, if it exists, is outside this slice's literal path and was not found.
- Whether a working removal route exists at a path shape not covered by this slice (e.g. a nested path under a different base, or a verb combined with a path segment we didn't try) — out of scope per "stay in your slice," but worth another slice/round checking paths like /api/v1/proj/<id>/remove or /api/v1/proj/delete.
- Field name for the project identifier on a removal call (id, project_id, pid, proj_id, projectId) — could not be distinguished because every attempt was rejected at the HTTP-method level (405) before any body/query parsing could occur, so no candidate could ever be "accepted."
- Whether GET /api/v1/proj/:id (the route actually matching /api/v1/proj/remove) returns full project detail for a valid id — not tested since it's outside this slice's endpoint list, but the 404 body shape `{"error":"no such project"}` for an invalid id was observed incidentally.

## Cleanup
- remove-fixture-1 (proj_8e63a5) → DELETE → HTTP 405 (not deleted; still present in GET /api/v1/proj?from=8 as of last check)
- remove-fixture-2 (proj_24200b) → DELETE → HTTP 405 (not deleted; still present in GET /api/v1/proj?from=8 as of last check)
