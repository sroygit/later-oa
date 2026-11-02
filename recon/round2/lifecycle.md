# Findings: r2-lifecycle (round 2)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 28 of 40

## POST /api/v1/proj/new

### Attempt 1
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-lifecycle-desc","description":"hello"}
Response: HTTP 201
```
{"description":"hello","id":"proj_b4460a","items":[],"status":"kickoff","title":"r2-lifecycle-desc","updated_at":1793579023819}
```
Note: description is accepted and echoed back on create.

### Attempt 2 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b4460a
Headers: none
Body: none
Response: HTTP 200
```
{"description":"hello","id":"proj_b4460a","items":[],"status":"kickoff","title":"r2-lifecycle-desc","updated_at":1793579023819}
```
Note: description persists in storage, confirmed via separate GET.

### Attempt 3
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":""}
Response: HTTP 400
```
{"error":"title is required"}
```
Note: empty string title is rejected (400), not accepted as a valid empty title. No project created, nothing to clean up.

## DELETE /api/v1/proj/{project_id}/remove

### Attempt 1 (fixture: r2-lifecycle-del)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-lifecycle-del"}
Response: HTTP 201
```
{"description":"","id":"proj_3cf951","items":[],"status":"kickoff","title":"r2-lifecycle-del","updated_at":1793579034057}
```

### Attempt 2
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_3cf951/remove
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"proj_3cf951"}
```

### Attempt 3 (same id, second delete)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_3cf951/remove
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: deleting an already-deleted project is not idempotent at the HTTP-status level — second delete is a 404.

### Attempt 4
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/does_not_exist/remove
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```
Note: same error body/shape as deleting an already-removed real id — "no such project" is the generic missing-project response, not specific to malformed ids.

### Attempt 5 (fixture: r2-lifecycle-slash)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-lifecycle-slash"}
Response: HTTP 201
```
{"description":"","id":"proj_b20782","items":[],"status":"kickoff","title":"r2-lifecycle-slash","updated_at":1793579046209}
```

### Attempt 6 (trailing slash)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782/remove/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: different error body than the "no such project" 404 — this is a routing miss (no route matches the trailing slash), not a project lookup failure.

### Attempt 7 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_b20782","items":[],"status":"kickoff","title":"r2-lifecycle-slash","updated_at":1793579046209}
```
Note: fixture survived the trailing-slash delete attempt, confirming attempt 6 never reached the delete handler.

### Attempt 8 (OPTIONS)
Request: OPTIONS https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782/remove
Headers: none
Body: none
Response: HTTP 200
```
(empty body)
Allow: DELETE, OPTIONS
```
Note: Allow header lists only DELETE and OPTIONS for this path — POST/PUT/PATCH/GET are not advertised as valid methods on /remove.

### Attempt 9 (POST instead of DELETE)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782/remove
Headers: none
Body: none
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: consistent with the Allow header in attempt 8 — POST does not delete.

### Attempt 10 (verification read)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782
Headers: none
Body: none
Response: HTTP 200
```
{"description":"","id":"proj_b20782","items":[],"status":"kickoff","title":"r2-lifecycle-slash","updated_at":1793579046209}
```
Note: project still exists after the failed POST — POST does not delete.

### Attempt 11 (cleanup of this fixture, proper route)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_b20782/remove
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"proj_b20782"}
```

### Attempt 12 (fixture: r2-lifecycle-count)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-lifecycle-count"}
Response: HTTP 201
```
{"description":"","id":"proj_128f07","items":[],"status":"kickoff","title":"r2-lifecycle-count","updated_at":1793579071636}
```

### Attempt 13 (baseline read, before remove)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=0
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[... 5 projects, truncated ...],"take":5,"total":11}
```
Note: total=11 just before removing proj_128f07 (7 seed projects + this slice's live fixture r2-lifecycle-desc + this count fixture + 2 fixtures belonging to other concurrently-running round-2 slices, not ours to touch).

### Attempt 14
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_128f07/remove
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"proj_128f07"}
```

### Attempt 15 (verification read, id)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_128f07
Headers: none
Body: none
Response: HTTP 404
```
{"error":"no such project"}
```

### Attempt 16 (verification read, list, after remove)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?from=0
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"projects":[... 5 projects, truncated ...],"take":5,"total":10}
```
Note: total dropped from 11 (attempt 13) to 10, confirming the remove decremented the live project count by exactly one.

## GET /api/v1/proj/{project_id}

### Attempt 1 (fixture: r2-lifecycle-putpatch)
Request: POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/new
Headers: Content-Type: application/json
Body: {"title":"r2-lifecycle-putpatch"}
Response: HTTP 201
```
{"description":"","id":"proj_49f13d","items":[],"status":"kickoff","title":"r2-lifecycle-putpatch","updated_at":1793579090636}
```

### Attempt 2 (PUT)
Request: PUT https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_49f13d
Headers: Content-Type: application/json
Body: {"title":"x"}
Response: HTTP 405
```
{"error":"method not allowed"}
```

### Attempt 3 (PATCH)
Request: PATCH https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_49f13d
Headers: Content-Type: application/json
Body: {"title":"x"}
Response: HTTP 405
```
{"error":"method not allowed"}
```
Note: /api/v1/proj/{id} only supports GET (and the nested action sub-paths); there is no in-place project-field update route on the plain id path via PUT or PATCH.

### Attempt 4 (cleanup of this fixture)
Request: DELETE https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/proj_49f13d/remove
Headers: none
Body: none
Response: HTTP 200
```
{"removed":"proj_49f13d"}
```

## GET /api/v1/proj

### Attempt 1 (take=5)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=5
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"take":5,"total":8,"projects":[... 5 entries ...]}
```
Note: echoed `take`=5, `projects` array length=5, `total`=8 (7 seed + this slice's still-live r2-lifecycle-desc fixture, deleted immediately after this test).

### Attempt 2 (take=4)
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj?take=4
Headers: none
Body: none
Response: HTTP 200
```
{"from":0,"take":4,"total":8,"projects":[... 4 entries ...]}
```
Note: echoed `take`=4, `projects` array length=4, same `total`=8 as attempt 1 — `take` only limits the page size, it does not affect the reported total.

## Could not determine
- Whether PUT/PATCH on /api/v1/proj/{id} would be accepted with a different body shape (e.g. a nested "project" wrapper) — only one body shape was tried before hitting 405, and 405 means the method itself is rejected by routing before any body is inspected, so further body variants would not change the outcome.
- Whether the double-delete 404 and the delete-nonexistent-id 404 share the exact same handler code path internally (both return byte-identical `{"error":"no such project"}`, strongly suggesting yes, but this was not verified via any header/trace distinguishing them).
- Whether the OPTIONS Allow header (`DELETE, OPTIONS`) is accurate for every project state, or whether it would change if the project did not exist (not tested: OPTIONS was only called on a live fixture).

## Cleanup
- r2-lifecycle-del (proj_3cf951) → DELETE → HTTP 200 (removed in attempt 2 of the remove section; second delete attempt correctly returned 404)
- r2-lifecycle-slash (proj_b20782) → DELETE → HTTP 200 (final cleanup in attempt 11 of the remove section, after trailing-slash and POST delete attempts both failed to remove it)
- r2-lifecycle-count (proj_128f07) → DELETE → HTTP 200
- r2-lifecycle-putpatch (proj_49f13d) → DELETE → HTTP 200
- r2-lifecycle-desc (proj_b4460a) → DELETE → HTTP 200 (removed last, after the take=5/take=4 list tests)
