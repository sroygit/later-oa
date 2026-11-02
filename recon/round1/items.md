# Findings: items (round 1)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app

Calls used: 40 of 40

## POST /api/v1/proj/new (fixture)

### Attempt 1
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title": "items-fixture-1"}
Response: HTTP 201
```
{"description":"","id":"proj_dc0698","items":[],"status":"kickoff","title":"items-fixture-1","updated_at":1793578016712}
```
Note: Accepted on first try with {"title": ...}. Project id format: `proj_` + 6 hex chars. `updated_at` is epoch-ms. Default status is "kickoff", items starts as [].

## GET /api/v1/proj/items

### Attempt 2
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/items
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: Route exists (distinct message from an unknown route's "not found"), but requires a project identifier.

### Attempt 3
Request: GET .../api/v1/proj/items?id=proj_dc0698
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 4
Request: GET .../api/v1/proj/items?project_id=proj_dc0698
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 5
Request: GET .../api/v1/proj/items?pid=proj_dc0698
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 6
Request: GET .../api/v1/proj/items?proj_id=proj_dc0698
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 7
Request: GET .../api/v1/proj/items?projectId=proj_dc0698
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 8
Request: GET .../api/v1/proj/items?title=items-fixture-1
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 9
Request: GET .../api/v1/proj/items?name=items-fixture-1
Response: HTTP 404
```
{"error":"no such project"}
```
Note: None of the 7 field-name candidates as query params worked — the project id is not passed via query string on this route at all.

### Attempt 23
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_dc0698/items
Headers: none
Body: none
Response: HTTP 200
```
{"items":[]}
```
Note: BREAKTHROUGH. The project id is a path segment: `/api/v1/proj/{project_id}/items`, not a query param on `/api/v1/proj/items`. The literal path given in the dispatch (`/api/v1/proj/items`) only works as an unparameterized route that always 404s "no such project".

### Attempt 24
Request: GET .../api/v1/proj/items with header `X-Project-Id: proj_dc0698`
Response: HTTP 404
```
{"error":"no such project"}
```
Note: Confirms header-based id also not supported; path segment is the only working mechanism found.

## POST /api/v1/proj/items/add

### Attempt 10
Request: POST .../api/v1/proj/items/add
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 11
Request: POST .../api/v1/proj/items/add
Headers: Content-Type: application/json
Body: {"id":"proj_dc0698","text":"wash dishes","person":"Alice","due_date":"2026-12-01"}
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 12
Request: POST .../api/v1/proj/items/add
Headers: Content-Type: application/json
Body: {"project_id":"proj_dc0698","text":"wash dishes"}
Response: HTTP 404
```
{"error":"not found"}
```
Note: All three bodies produce the identical generic "not found" — suspicious that the literal path doesn't exist at all (see attempt 13 control).

### Attempt 13 (diagnostic control)
Request: POST .../api/v1/proj/items/totally-bogus-path
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: Identical error/status to attempts 10-12, confirming `/api/v1/proj/items/add` is treated the same as a nonexistent route, not a recognized route with a missing/bad project.

### Attempt 14
Request: POST .../api/v1/proj/items/add/ (trailing slash)
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 15
Request: GET .../api/v1/proj/items/add
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 16
Request: PUT .../api/v1/proj/items/add
Response: HTTP 404
```
{"error":"not found"}
```
Note: Same "not found" across GET/POST/PUT — rules out "wrong HTTP method on a real route" (a real-but-wrong-method route returns 405, see attempts 17/18 below), confirming the literal path truly does not exist on the server.

### Attempt 17 (diagnostic control)
Request: POST .../api/v1/proj/items (no body)
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Proves the server DOES distinguish "route exists, wrong method" (405) from "route doesn't exist" (404 "not found"). This validates the conclusion in attempt 16.

### Attempt 18 (diagnostic control)
Request: POST .../api/v1/proj/items
Headers: Content-Type: application/json
Body: {"id":"proj_dc0698","text":"wash dishes"}
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 25
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_dc0698/items/add
Headers: none
Body: none
Response: HTTP 400
```
{"error":"task is required"}
```
Note: Real route is nested: `/api/v1/proj/{project_id}/items/add`. Error names the required field: `task`.

### Attempt 26
Request: POST .../api/v1/proj/proj_dc0698/items/add
Headers: Content-Type: application/json
Body: {"task":"wash dishes"}
Response: HTTP 201
```
{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}
```
Note: Todo id format: `todo_` + 6 hex chars. Default `who` is `""`. Default `by` when omitted is an epoch-ms integer (looked like call time, i.e. "now", not a far-future default) — `by` is NOT required despite being a plausible due-date field.

### Attempt 27
Request: POST .../api/v1/proj/proj_dc0698/items/add
Headers: Content-Type: application/json
Body: {"task":"buy milk","who":"Alice","by":"2026-12-01"}
Response: HTTP 201
```
{"by":"2026-12-01","done":false,"id":"todo_bedcfc","task":"buy milk","who":"Alice"}
```
Note: `who` and `by` both accepted verbatim, no type coercion/validation observed — `by` stored as the literal string "2026-12-01" when given a date string, vs. an epoch-ms number when defaulted. Field is schema-less / accepts either shape.

### Attempt 28 (verification read)
Request: GET .../api/v1/proj/proj_dc0698/items
Response: HTTP 200
```
{"items":[{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""},{"by":"2026-12-01","done":false,"id":"todo_bedcfc","task":"buy milk","who":"Alice"}]}
```
Note: Both added todos persisted exactly as returned by /add, confirming /add's response body mirrors the stored record.

## POST /api/v1/proj/items/mark

### Attempt 19
Request: POST .../api/v1/proj/items/mark
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 21
Request: GET .../api/v1/proj/items/mark
Response: HTTP 404
```
{"error":"not found"}
```
Note: Same "not found" pattern as the add route — literal path from the dispatch does not exist.

### Attempt 29
Request: POST .../api/v1/proj/proj_dc0698/items/mark (nested project path, no body)
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 30
Request: POST .../api/v1/proj/proj_dc0698/items/mark
Headers: Content-Type: application/json
Body: {"id":"todo_fec6bd"}
Response: HTTP 404
```
{"error":"not found"}
```
Note: Nesting only the project id isn't enough — the todo id must also be a path segment (see attempt 31).

### Attempt 31
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_dc0698/items/todo_fec6bd/mark
Headers: none
Body: none
Response: HTTP 400
```
{"error":"flag must be 'yes' or 'no'"}
```
Note: Real route is doubly-nested: `/api/v1/proj/{project_id}/items/{todo_id}/mark`. Required field is `flag`, an enum of the literal strings "yes"/"no" (not a boolean).

### Attempt 32
Request: POST .../api/v1/proj/proj_dc0698/items/todo_fec6bd/mark
Headers: Content-Type: application/json
Body: {"flag":"yes"}
Response: HTTP 200
```
{"by":1793578132540,"done":true,"id":"todo_fec6bd","task":"wash dishes","who":""}
```

### Attempt 33 (verification read)
Request: GET .../api/v1/proj/proj_dc0698/items
Response: HTTP 200
```
{"items":[{"by":1793578132540,"done":true,"id":"todo_fec6bd","task":"wash dishes","who":""},{"by":"2026-12-01","done":false,"id":"todo_bedcfc","task":"buy milk","who":"Alice"}]}
```
Note: Confirms done:true persisted for todo_fec6bd only.

### Attempt 34
Request: POST .../api/v1/proj/proj_dc0698/items/todo_fec6bd/mark (same todo, same flag, called again)
Headers: Content-Type: application/json
Body: {"flag":"yes"}
Response: HTTP 200
```
{"by":1793578132540,"done":true,"id":"todo_fec6bd","task":"wash dishes","who":""}
```
Note: Calling with the same flag twice leaves done:true unchanged — this is a SET operation, not a toggle.

### Attempt 35
Request: POST .../api/v1/proj/proj_dc0698/items/todo_fec6bd/mark
Headers: Content-Type: application/json
Body: {"flag":"no"}
Response: HTTP 200
```
{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}
```
Note: Confirms `mark` explicitly sets `done` to true/false based on `flag`, in either direction. Definitively not a toggle.

## DELETE /api/v1/proj/items/yank

### Attempt 20
Request: DELETE .../api/v1/proj/items/yank
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 22
Request: GET .../api/v1/proj/items/yank
Response: HTTP 404
```
{"error":"not found"}
```
Note: Literal path from the dispatch does not exist, same pattern as add/mark.

### Attempt 36
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_dc0698/items/todo_bedcfc/yank
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"todo_bedcfc"}
```
Note: Real route follows the same doubly-nested pattern as mark: `/api/v1/proj/{project_id}/items/{todo_id}/yank`. No body needed; worked on first try (no param search required).

### Attempt 37 (verification read)
Request: GET .../api/v1/proj/proj_dc0698/items
Response: HTTP 200
```
{"items":[{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}]}
```
Note: todo_bedcfc removed; todo_fec6bd remains, confirming yank deletes exactly the targeted todo.

## DELETE /api/v1/proj/remove (fixture cleanup)

### Attempt 38
Request: DELETE .../api/v1/proj/remove?id=proj_dc0698
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: Route exists (405, not 404) but DELETE is the wrong method here.

### Attempt 39
Request: POST .../api/v1/proj/remove
Headers: Content-Type: application/json
Body: {"id":"proj_dc0698"}
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: POST also rejected with 405 for this literal path — same nested-path pattern as items/add/mark/yank was tried next.

### Attempt 40
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_dc0698/remove
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"proj_dc0698"}
```
Note: Real cleanup route is `DELETE /api/v1/proj/{project_id}/remove` (project id as path segment, matching the items/add/mark/yank pattern). This was the final call in the 40-call budget, used to clean up the fixture project.

## Could not determine

- Whether `/api/v1/proj/items`, `/api/v1/proj/items/add`, `/api/v1/proj/items/mark`, `/api/v1/proj/items/yank`, and `/api/v1/proj/remove` (the literal paths from the dispatch) have ANY other accepted shape besides the nested-path pattern discovered — ran out of budget to confirm e.g. a `?id=` variant also works on the nested-add/mark/yank/remove routes, or whether query-string project id works anywhere at all.
- What the accepted date formats for `by` actually are beyond "any string is stored verbatim, no validation observed" — try an invalid-looking date (e.g. "not-a-date") or a negative/huge number to see if there is ANY validation.
- What happens when `add`/`mark`/`yank` are called with a project id that does not exist (never tested against a bad project id with the correct nested-route shape — only tested against the real fixture project). Try `/api/v1/proj/doesnotexist/items/add`.
- What happens when `mark`/`yank` are called with a todo id that does not exist within a real project. Try `/api/v1/proj/proj_xxx/items/todo_bogus/mark`.
- Whether `mark`'s `flag` field is case-sensitive (e.g. does "Yes"/"YES"/"true"/true work, or only lowercase "yes"/"no" strings) — not tested due to budget.
- Whether `add` validates `who`/`by` types (e.g. a number for `who`, or rejects malformed `by`) — not tested due to budget.
- Whether trailing slash matters on the real nested routes (only tested trailing slash on the non-existent literal `/add` path, not on the working nested path).
- Whether GET /api/v1/proj/items (literal, unparameterized) ever returns anything other than "no such project" under any input — possible it's dead code / always errors.

## Cleanup
- items-fixture-1 (proj_dc0698) → DELETE /api/v1/proj/proj_dc0698/remove → HTTP 200 (`{"removed":"proj_dc0698"}`) — succeeded.
