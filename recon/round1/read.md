# Findings: read (round 1)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 23 of 40

## GET /api/v1/health

### Attempt 1
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/health
Headers: none
Body: none
Response: HTTP 200
```
{"status":"ok"}
```

### Attempt 2 (edge case: trailing slash)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/health/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: trailing slash is not tolerated; router does exact-path matching.

## GET /api/v1/proj

### Attempt 1 (no params)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{"description":"Public launch of v3. Coordinate marketing, eng, and CS.","id":"proj_23315f","items":[{"by":1793750085470,"done":false,"id":"todo_9e5e55","task":"Finalize launch blog post","who":"betty"},{"by":1793922885470,"done":false,"id":"todo_76344a","task":"QA the onboarding flow on staging","who":"carlos"},{"by":1793836485470,"done":true,"id":"todo_68ddc7","task":"Draft launch-day Slack post","who":"andy"},{"by":1794095685470,"done":false,"id":"todo_a5c40c","task":"Update the help center landing page","who":"dan"}],"status":"wip","title":"Spring product launch","updated_at":1793577285470},{"description":"Two-week paid pilot. Single tenant. Slack channel #acme-pilot.","id":"proj_756702","items":[{"by":1793663685470,"done":true,"id":"todo_bb91e0","task":"Send kickoff doc","who":"dan"},{"by":1793750085470,"done":false,"id":"todo_1ed113","task":"Schedule weekly sync","who":"carlos"},{"by":1793836485470,"done":false,"id":"todo_c25ab8","task":"Provision sandbox tenant","who":"betty"}],"status":"kickoff","title":"Enterprise pilot, Acme Co.","updated_at":1793577285470},{"description":"Cutover to the new payment processor. Coordinate with finance.","id":"proj_ad713f","items":[{"by":1793404485470,"done":false,"id":"todo_cc8e4e","task":"Get final sign-off from finance","who":"carlos"},{"by":1794182085470,"done":false,"id":"todo_8408ac","task":"Backfill historical invoices","who":"betty"}],"status":"blocked","title":"Migrate billing to new processor","updated_at":1793577285470},{"description":"Get internal teams onto the new AI tooling stack.","id":"proj_338616","items":[{"by":1794009285470,"done":false,"id":"todo_3b73e0","task":"Run training session for ops","who":"andy"},{"by":1793922885470,"done":false,"id":"todo_cccb9a","task":"Write the FAQ doc","who":"dan"},{"by":1794441285470,"done":false,"id":"todo_8900c1","task":"Collect feedback from beta users","who":"betty"},{"by":1794786885470,"done":false,"id":"todo_eaafa9","task":"Cancel legacy seats","who":"carlos"}],"status":"wip","title":"Internal AI tooling rollout","updated_at":1793577285470},{"description":"Light brand refresh. New typography and color tokens.","id":"proj_e869bb","items":[{"by":1792713285470,"done":true,"id":"todo_cf1cd1","task":"Update marketing site","who":"betty"},{"by":1793145285470,"done":true,"id":"todo_ec3312","task":"Roll new logo to all repos","who":"dan"}],"status":"wrapped","title":"Q2 brand refresh","updated_at":1793577285470}],"take":5,"total":10}
```
Note: default page is 5 projects, `total` was 10 at this moment (grows as parallel probers create fixtures).

### Attempt 2 (query param: from=5)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":5,"projects":[{"description":"Reduce time-to-first-value from 7 days to 2.","id":"proj_828748","items":[{"by":1793836485470,"done":false,"id":"todo_5d9f01","task":"Interview 5 recent signups","who":"carlos"},{"by":1794009285470,"done":false,"id":"todo_6bf0ca","task":"Audit current funnel drop-off","who":"betty"}],"status":"kickoff","title":"Customer onboarding redesign","updated_at":1793577285470},{"description":"Move from manual schedule to PagerDuty.","id":"proj_bd0d1e","items":[{"by":1790985285470,"done":false,"id":"todo_0fa167","task":"Get budget approval","who":"carlos"}],"status":"dropped","title":"On-call rotation revamp","updated_at":1793577285470},{"description":"","id":"proj_dc0698","items":[],"status":"kickoff","title":"items-fixture-1","updated_at":1793578016712},{"description":"","id":"proj_8e63a5","items":[],"status":"kickoff","title":"remove-fixture-1","updated_at":1793578020876},{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}],"take":5,"total":11}
```
Note: `from` offsets pagination; three fixture projects created by other probers (items-fixture-1, remove-fixture-1, write-probe-1) are visible here — not created by me, left untouched.

### Attempt 3 (query param: take=2)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=2
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{...proj_23315f...},{...proj_756702...}],"take":2,"total":11}
```
Note: [truncated — same two project objects as Attempt 1, abbreviated here]. `take` is respected when ≤5.

### Attempt 4 (query params: from=5&take=5)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=5&take=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":5,"projects":[{...proj_828748...},{...proj_bd0d1e...},{...proj_dc0698...},{...proj_8e63a5...},{...proj_aa6cb4...}],"take":5,"total":11}
```
Note: [truncated, same 5 objects as Attempt 2]. Combining from+take works as expected pagination.

### Attempt 5 (query param: id=proj_23315f — field candidate, no trailing slash)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?id=proj_23315f
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{...5 projects, same as default page...}],"take":5,"total":12}
```
Note: `id` query param on the list endpoint is silently ignored — no filtering occurs, default page returned.

### Attempt 6 (query param: status=wip — filter attempt)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?status=wip
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{...5 projects, identical to default page...}],"take":5,"total":12}
```
Note: `status` query param is also ignored — no server-side filtering by status exists on this endpoint.

### Attempt 7 (edge case: take=0)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=0
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[],"take":0,"total":13}
```

### Attempt 8 (edge case: take=100, larger than available)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=100
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{...5 projects, same as default page...}],"take":5,"total":13}
```
Note: `take` is capped at 5 — requesting 100 silently returns only 5 and echoes `"take":5`, not 100.

### Attempt 9 (edge case: take=abc, wrong type)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=abc
Headers: none
Body: none
Response: HTTP 400
```
{"error":"from/take must be integers"}
```
Note: type validation exists and names both `from` and `take` in one error message.

### Attempt 10 (edge case: from=-1, negative)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=-1
Headers: none
Body: none
Response: HTTP 200
```
{"from":-1,"projects":[],"take":5,"total":13}
```
Note: negative `from` is accepted (no 400) but yields an empty `projects` array; `from` is echoed back as -1.

### Attempt 11 (confirm take cap: take=6)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=6
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[{...5 projects, same as default page...}],"take":5,"total":13}
```
Note: confirms max page size is exactly 5 regardless of requested `take` above that.

## GET /api/v1/proj/ (trailing slash)

### Attempt 1 (no params)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 2 (query param: id=proj_23315f)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/?id=proj_23315f
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 3 (query param: project_id=proj_23315f)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/?project_id=proj_23315f
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 4 (query param: pid=proj_23315f)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/?pid=proj_23315f
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 5 (query param: proj_id=proj_23315f)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/?proj_id=proj_23315f
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 6 (query param: projectId=proj_23315f)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/?projectId=proj_23315f
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: `/api/v1/proj/` (trailing slash) returns the identical 404 `{"error":"not found"}` regardless of any query parameter — this is a plain route-not-found, not an endpoint that reads query params at all. This differs from `/api/v1/proj` (no slash), which is the real list endpoint and always returns HTTP 200.

## GET /api/v1/proj/{id} (path segment — observed by exploring the 404 boundary of /api/v1/proj/)

### Attempt 1 (valid id as path segment)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_23315f
Headers: none
Body: none
Response: HTTP 200
```
{"description":"Public launch of v3. Coordinate marketing, eng, and CS.","id":"proj_23315f","items":[{"by":1793750085470,"done":false,"id":"todo_9e5e55","task":"Finalize launch blog post","who":"betty"},{"by":1793922885470,"done":false,"id":"todo_76344a","task":"QA the onboarding flow on staging","who":"carlos"},{"by":1793836485470,"done":true,"id":"todo_68ddc7","task":"Draft launch-day Slack post","who":"andy"},{"by":1794095685470,"done":false,"id":"todo_a5c40c","task":"Update the help center landing page","who":"dan"}],"status":"wip","title":"Spring product launch","updated_at":1793577285470}
```
Note: `/api/v1/proj/<id>` IS a real route (single-project fetch, full detail with items) — distinct from `/api/v1/proj/` which is just a 404. This is outside the dispatched ENDPOINTS list but was reached incidentally while probing `/api/v1/proj/`'s 404 boundary per the dispatch instruction to "try GET /api/v1/proj/<id> as a path segment once."

### Attempt 2 (edge case: trailing slash on path-segment form)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_23315f/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```

### Attempt 3 (edge case: id that does not exist)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/does_not_exist
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: different error body than the plain route-404 (`"no such project"` vs `"not found"`) — this confirms `/api/v1/proj/<id>` is a real handler that does its own existence check, unlike `/api/v1/proj/` which never reaches a handler.

### Attempt 4 (edge case: enum/case variant — uppercase id)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/PROJ_23315F
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: project ids are case-sensitive; uppercasing a valid id makes it "no such project".

## Could not determine
- Whether `/api/v1/proj/<id>` supports any query params (id/field candidates) — not tested, since it is outside this slice's dispatched ENDPOINTS list (GET /api/v1/health, GET /api/v1/proj, GET /api/v1/proj/); only the one path-segment probe explicitly requested by the dispatch was done.
- Whether `from`/`take` have an independently-settable max above 5, or whether 5 is hard-coded — try `take=5` exactly vs `take=4` to confirm the ceiling is exactly 5 and not, e.g., dependent on `total`.
- Why `from=-1` returns HTTP 200 with an empty array instead of either erroring or wrapping/clamping to 0 — try `from=-2`, `from=-5` to see if behavior is uniform for all negatives.
- Whether any other query param name (e.g. `status`, `title`, `q`, `search`) triggers real filtering on `/api/v1/proj` — only `id` and `status` were tried and both were ignored.
- The exact set of valid `status` enum values (seen in data: `wip`, `kickoff`, `blocked`, `wrapped`, `dropped`) — no endpoint in this slice lets us test enum validation since status isn't accepted as a filter or write field here.
- `total` changed from 10 → 11 → 12 → 13 across the session because other probers (slices `write-`, `remove-`, `items-`) were creating projects concurrently; the list is not a stable snapshot during round 1.

## Cleanup
- No projects were created by this slice (read-only slice, no fixtures used). Nothing to delete.
