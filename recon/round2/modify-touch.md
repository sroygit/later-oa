# Findings: r2-modify-touch (round 2)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 20 of 40 (20 of 25 target budget)

## PUT /api/v1/proj/{project_id}/modify

### Attempt 1 (modify Q1: rename title)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {"title":"r2-modify-touch-1-renamed"}
Response: HTTP 200
```
{"description":"","id":"proj_72c717","items":[],"status":"kickoff","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: PUT succeeded directly (no 405), so OPTIONS/POST/PATCH fallback (Q2) was not needed.

### Attempt 2 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_72c717","items":[],"status":"kickoff","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: Title changed to the new value, but `updated_at` stayed exactly 1793579008014, the same value set at project creation — modify did NOT bump updated_at.

### Attempt 3 (modify Q3: status=wrapped)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {"status":"wrapped"}
Response: HTTP 200
```
{"description":"","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: status updated to "wrapped" (lowercase enum value accepted); updated_at still unchanged.

### Attempt 4 (modify Q3: status=WIP, different case)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {"status":"WIP"}
Response: HTTP 400
```
{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}
```
Note: Same case-sensitive enum rejection pattern as /new. Full valid enum set revealed: blocked, dropped, kickoff, wip, wrapped (all lowercase).

### Attempt 5 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: status remains "wrapped" from attempt 3 (the rejected WIP attempt had no effect).

### Attempt 6 (modify Q4: description)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {"description":"r2 description"}
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: description is updatable through modify.

### Attempt 7 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```

### Attempt 8 (modify Q5: empty body)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {}
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: Empty body is NOT a 400 — it returns 200 with the project completely unchanged. No required fields are enforced on modify.

### Attempt 9 (modify Q6: nonexistent project)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/does_not_exist/modify
Headers: Content-Type: application/json
Body: {"title":"x"}
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 10 (modify Q7 setup: add a todo item, (fixture side-effect, not tagged fixture since it's a real items/add call))
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/items/add
Headers: Content-Type: application/json
Body: {"task":"t"}
Response: HTTP 201
```
{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}
```
Note: Todo id format `todo_<6 hex chars>`. `by` field is a millisecond epoch timestamp (creation time), `who` defaults to empty string.

### Attempt 11 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: item present in items array; project's own updated_at still unchanged even after adding an item.

### Attempt 12 (modify Q7: items=[] to try wiping items)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/modify
Headers: Content-Type: application/json
Body: {"items":[]}
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: `items` field silently ignored — the existing todo is still present. No error; modify cannot wipe items.

### Attempt 13 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}
```
Note: Confirms items array unchanged by the modify items=[] attempt.

## POST /api/v1/proj/{project_id}/touch

### Attempt 1 (touch Q1: no body, after 1s sleep)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/touch
Headers: none
Body: none
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579049851}
```
Note: POST succeeded directly (no 405), so OPTIONS/PUT/PATCH fallback (touch Q2) was not needed. updated_at increased from 1793579008014 to 1793579049851 (confirms touch bumps updated_at, which modify never did across 4 prior calls).

### Attempt 2 (verification read, confirms Attempt 1's updated_at persists)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717
Headers: none
Body: none
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579049851}
```

### Attempt 3 (touch Q3: body with status/title)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_72c717/touch
Headers: Content-Type: application/json
Body: {"status":"wip","title":"touched"}
Response: HTTP 200
```
{"description":"r2 description","id":"proj_72c717","items":[{"by":1793579034933,"done":false,"id":"todo_a83729","task":"t","who":""}],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579056134}
```
Note: Body fields entirely ignored — status stayed "wrapped" and title stayed "r2-modify-touch-1-renamed"; only updated_at was bumped again (1793579049851 → 1793579056134). Touch's only effect is bumping updated_at.

### Attempt 4 (touch Q4: nonexistent project)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/does_not_exist/touch
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: Identical error shape to modify's nonexistent-project case.

## Could not determine
- Whether PUT /modify would have returned 405 on some other field combination was not tested — PUT worked on the first try for every field tried (title, status, description, items), so the OPTIONS/POST/PATCH fallback path was never exercised. If a future slice needs the Allow header for /modify, it has not been recorded.
- Whether POST /touch would have returned 405 under different conditions was not tested either, for the same reason — it worked immediately with and without a body.
- Whether modify can remove/clear a todo item through some other field name (e.g. `remove_items`, `delete_items`) besides `items: []` was not tried — only the literal `items: []` shape from the dispatch was tested.
- Whether touch has any effect at all when given a body containing fields not seen elsewhere (e.g. `description`, `items`) is unconfirmed beyond the `status`/`title` combination tested — but given it fully ignored those two, it's a reasonable inference (not recorded as a finding) that it ignores all body fields.
- Exact id format confirmed only from this one fixture: project ids are `proj_<6 hex chars>` (e.g. `proj_72c717`), todo ids are `todo_<6 hex chars>` (e.g. `todo_a83729`). `updated_at` and the todo `by` field are both millisecond epoch integers (13 digits, e.g. 1793579008014).

## Cleanup
- r2-modify-touch-1-renamed (proj_72c717) → DELETE /api/v1/proj/proj_72c717/remove → HTTP 200, body {"removed":"proj_72c717"}
