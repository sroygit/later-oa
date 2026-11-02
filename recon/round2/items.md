# Findings: r2-items (round 2)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 27 of 30 (30 was the round-specific budget; hard cap is 40)

## (fixture) POST /api/v1/proj/new

### Attempt 1
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-items-1"}
Response: HTTP 201
```
{"description":"","id":"proj_a981de","items":[],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```
Note: project id format is `proj_<6 hex chars>`; updated_at is epoch millis.

### Attempt 2
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-items-2"}
Response: HTTP 201
```
{"description":"","id":"proj_50ed03","items":[],"status":"kickoff","title":"r2-items-2","updated_at":1793579030243}
```

## POST /api/v1/proj/{project_id}/items/add

### Attempt 1 (section 1a: by="not-a-date")
Request: POST .../api/v1/proj/proj_a981de/items/add
Headers: Content-Type: application/json
Body: {"task":"x","by":"not-a-date"}
Response: HTTP 201
```
{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""}
```
Note: no validation on `by` — stored verbatim as the string given.

### Attempt 2 (section 1b: by=-1)
Request: POST .../api/v1/proj/proj_a981de/items/add
Headers: Content-Type: application/json
Body: {"task":"x","by":-1}
Response: HTTP 201
```
{"by":-1,"done":false,"id":"todo_7b4ab9","task":"x","who":""}
```
Note: negative number also accepted verbatim, no type/range check.

### Attempt 3 (section 1c: who=123)
Request: POST .../api/v1/proj/proj_a981de/items/add
Headers: Content-Type: application/json
Body: {"task":"x","who":123}
Response: HTTP 201
```
{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123}
```
Note: `who` (number 123) accepted verbatim; `by` omitted so server defaulted it to current epoch millis — confirms `by` is the "assigned/created" timestamp field and `who` is the free-form assignee field (unvalidated type).

### Attempt 4 (section 2: done=true at creation)
Request: POST .../api/v1/proj/proj_a981de/items/add
Headers: Content-Type: application/json
Body: {"task":"x","done":true}
Response: HTTP 201
```
{"by":1793579036855,"done":false,"id":"todo_4f80e4","task":"x","who":""}
```
Note: `done` cannot be set at creation — request sent done:true, server returned done:false (silently ignored/forced false).

### Attempt 5 (section 3: GET before add)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":false,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123},{"by":1793579036855,"done":false,"id":"todo_4f80e4","task":"x","who":""}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```

### Attempt 6 (section 3: add after 1s sleep)
Request: POST .../api/v1/proj/proj_a981de/items/add
Headers: Content-Type: application/json
Body: {"task":"check-update","who":"tester"}
Response: HTTP 201
```
{"by":1793579044790,"done":false,"id":"todo_7163b6","task":"check-update","who":"tester"}
```

### Attempt 7 (section 3: GET after add) (verification read)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":false,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123},{"by":1793579036855,"done":false,"id":"todo_4f80e4","task":"x","who":""},{"by":1793579044790,"done":false,"id":"todo_7163b6","task":"check-update","who":"tester"}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```
Note: `items` array correctly includes the new todo, but the project's `updated_at` (1793579030135) did NOT change after adding an item — it stayed at creation time.

## POST /api/v1/proj/{project_id}/items/{todo_id}/mark

### Attempt 1 (section 1: flag="Yes")
Request: POST .../api/v1/proj/proj_a981de/items/todo_265c4d/mark
Headers: Content-Type: application/json
Body: {"flag":"Yes"}
Response: HTTP 400
```
{"error":"flag must be 'yes' or 'no'"}
```

### Attempt 2 (section 1: flag=true, boolean)
Request: POST .../api/v1/proj/proj_a981de/items/todo_265c4d/mark
Headers: Content-Type: application/json
Body: {"flag":true}
Response: HTTP 400
```
{"error":"flag must be 'yes' or 'no'"}
```

### Attempt 3 (section 1: flag="true", string)
Request: POST .../api/v1/proj/proj_a981de/items/todo_265c4d/mark
Headers: Content-Type: application/json
Body: {"flag":"true"}
Response: HTTP 400
```
{"error":"flag must be 'yes' or 'no'"}
```

### Attempt 4 (section 1: flag=1, number)
Request: POST .../api/v1/proj/proj_a981de/items/todo_265c4d/mark
Headers: Content-Type: application/json
Body: {"flag":1}
Response: HTTP 400
```
{"error":"flag must be 'yes' or 'no'"}
```
Note: all four variants (Yes / true bool / "true" string / 1 number) rejected with the identical message; only the exact lowercase strings "yes"/"no" are accepted (confirmed below).

### Attempt 5 (section 2: todo_bogus)
Request: POST .../api/v1/proj/proj_a981de/items/todo_bogus/mark
Headers: Content-Type: application/json
Body: {"flag":"yes"}
Response: HTTP 404
```
{"error":"no such item"}
```

### Attempt 6 (section 3: cross-project scope — proj2's path, todo belongs to proj1)
Request: POST .../api/v1/proj/proj_50ed03/items/todo_265c4d/mark
Headers: Content-Type: application/json
Body: {"flag":"yes"}
Response: HTTP 404
```
{"error":"no such item"}
```
Note: project scope IS enforced — marking a valid todo id via the wrong project's path returns the same "no such item" 404 as a bogus todo id, i.e. todo lookup is scoped to the project in the path, not global.

### Attempt 7 (section 4: GET before mark)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":false,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123},{"by":1793579036855,"done":false,"id":"todo_4f80e4","task":"x","who":""},{"by":1793579044790,"done":false,"id":"todo_7163b6","task":"check-update","who":"tester"}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```

### Attempt 8 (section 4: valid mark after 1s sleep)
Request: POST .../api/v1/proj/proj_a981de/items/todo_7b4ab9/mark
Headers: Content-Type: application/json
Body: {"flag":"yes"}
Response: HTTP 200
```
{"by":-1,"done":true,"id":"todo_7b4ab9","task":"x","who":""}
```
Note: lowercase "yes" is accepted and flips `done` to true.

### Attempt 9 (section 4: GET after mark) (verification read)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":true,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123},{"by":1793579036855,"done":false,"id":"todo_4f80e4","task":"x","who":""},{"by":1793579044790,"done":false,"id":"todo_7163b6","task":"check-update","who":"tester"}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```
Note: `updated_at` again did NOT change (still 1793579030135) despite the mark changing the todo's `done` field — same behavior as items/add.

## DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank

### Attempt 1 (section 1: first yank)
Request: DELETE .../api/v1/proj/proj_a981de/items/todo_4f80e4/yank
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"todo_4f80e4"}
```

### Attempt 2 (section 1: second yank, same todo)
Request: DELETE .../api/v1/proj/proj_a981de/items/todo_4f80e4/yank
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such item"}
```
Note: yank is not idempotent — the second call on an already-removed todo returns 404, same message as a never-existed id.

### Attempt 3 (section 2: cross-project scope — proj2's path, todo belongs to proj1)
Request: DELETE .../api/v1/proj/proj_50ed03/items/todo_48cde3/yank
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such item"}
```
Note: yank is also project-scoped — refused with the same "no such item" 404 as a nonexistent id, consistent with mark's scoping.

### Attempt 4 (section 3: GET before yank)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":true,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123},{"by":1793579044790,"done":false,"id":"todo_7163b6","task":"check-update","who":"tester"}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```

### Attempt 5 (section 3: yank after 1s sleep)
Request: DELETE .../api/v1/proj/proj_a981de/items/todo_7163b6/yank
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"todo_7163b6"}
```

### Attempt 6 (section 3: GET after yank) (verification read)
Request: GET .../api/v1/proj/proj_a981de
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_a981de","items":[{"by":"not-a-date","done":false,"id":"todo_265c4d","task":"x","who":""},{"by":-1,"done":true,"id":"todo_7b4ab9","task":"x","who":""},{"by":1793579036751,"done":false,"id":"todo_48cde3","task":"x","who":123}],"status":"kickoff","title":"r2-items-1","updated_at":1793579030135}
```
Note: todo removed from `items`, but `updated_at` still did not change — confirms project `updated_at` is never bumped by any items sub-resource mutation (add, mark, or yank) observed in this slice.

## GET /api/v1/proj/{project_id}/items

### Attempt 1 (section 1: nonexistent project)
Request: GET .../api/v1/proj/does_not_exist/items
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

## Could not determine
- Whether `updated_at` is ever bumped by anything at all (it stayed constant across add/mark/yank in every test here) — try PUT/PATCH on the project's own title/description/status fields directly to see if `updated_at` changes for non-items mutations.
- Whether any flag value other than exact lowercase "yes"/"no" is accepted for mark (e.g. "no", or whitespace-padded "yes ") — only the rejects were tested here besides one plain "yes".
- Exact shape of the dedicated `GET /api/v1/proj/{project_id}/items` endpoint's success response (only its 404-on-missing-project case was tested per the round-2 question list; its 200 shape was inferred only via `GET /api/v1/proj/{project_id}` which embeds items, never called directly).

## Cleanup
- r2-items-1 (proj_a981de) → DELETE /api/v1/proj/proj_a981de/remove → HTTP 200 (`{"removed":"proj_a981de"}`)
- r2-items-2 (proj_50ed03) → DELETE /api/v1/proj/proj_50ed03/remove → HTTP 200 (`{"removed":"proj_50ed03"}`)
