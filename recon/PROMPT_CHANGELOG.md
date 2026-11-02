# Prober prompt changelog

Appended by the reviewer agent after each round. One entry per rewrite.

Entry format:

```
## <ISO-8601 time> — after round <n>

### Change 1: <short title>
Observed failure: <what the probers did badly, citing recon/round<n>/<file>.md attempt numbers>
Before:
> <old instruction text>
After:
> <new instruction text>
Why: <one sentence>
```

## 2026-11-02T00:03:00Z — after round 0

No changes. Probers followed the protocol and the unresolved items need round-two targeting, not better instructions.

## 2026-11-02T00:19:00Z — after round 1

### Change 1: Try the nested path shape before sweeping field names
Observed failure: three of four probers burned most of their budget on the flat paths from the brief, which never exist as literal routes. remove.md#Attempt 1-23 spent all 31 calls on flat `/api/v1/proj/remove` (every method, header, and field variant) and never tried `/api/v1/proj/{id}/remove`. items.md#Attempt 2-9 swept 8 query-param field names on flat `/api/v1/proj/items` (all 404 "no such project") and did not reach the nested path until items.md#Attempt 23. write.md#Attempt 1-13 (modify) and Attempt 1-6 (touch) stayed on the flat paths and never tried `/api/v1/proj/{id}/modify` or `/touch`.
Before:
> 2. If it is a GET or DELETE, try parameters as query string. If it is a POST or PUT, try a JSON body, then a form body, then query string.
> 3. Field name candidates, try in this order until one is accepted:
After:
> 2. **Path shape before field-name sweep.** The paths in `ENDPOINTS` are operation labels, not guaranteed literal routes. The moment a flat path returns 404 (`no such project` or `not found`) or 405, put the ids in the path and retry the nested shape before sweeping any query or body field names: `/api/v1/proj/{project_id}`, `/api/v1/proj/{project_id}/<action>`, and for todo actions `/api/v1/proj/{project_id}/items/{todo_id}/<action>`. Only once a path shape gets past routing (a 200, a 201, or a field-level 400 that names a required field) do you move on.
> 3. Sweep field names only for whatever body or query remains on a working path shape. For a GET or DELETE put parameters in the query string; for a POST or PUT try a JSON body, then a form body, then query string. Field-name candidates, in order until one is accepted:
Why: The single biggest round-1 waste was sweeping params and methods on paths that 404/405 because the id belongs in the path, so the path-shape test must come first.

### Change 2: Cap probing of a single dead flat path in the budget rule
Observed failure: remove.md#Attempt 1-23 spent 31 of 40 calls hammering one flat path (`/api/v1/proj/remove`) with method, header, and field permutations that all returned 405, instead of stopping after a few and moving to the nested shape; items.md#Attempt 2-9 similarly exhausted the field-name list on flat `/items` before the Attempt 23 breakthrough.
Before:
> 5. **Budget: at most 40 curl calls.** Count them. Stop at 40 and write what you have.
After:
> 5. **Budget: at most 40 curl calls.** Count them. Stop at 40 and write what you have. Do not spend more than 3 calls probing a single flat path from `ENDPOINTS`: if it returns 404 or 405, the id almost certainly belongs in the path (see Protocol step 2), so switch to the nested shape instead of sweeping more methods, headers, or field names on a dead flat path.
Why: A hard per-path cap forces the path-shape sweep early and stops a single dead flat path from eating the whole budget.

### Change 3: Point the cleanup fixture call at the real nested remove route
Observed failure: the fixture section told probers to clean up with flat `DELETE /api/v1/proj/remove`, which is not a delete route. remove.md#Cleanup left remove-fixture-1 and remove-fixture-2 undeleted (every DELETE returned 405), and write.md#Cleanup left all three created projects on the server; both had to be cleaned up afterward by the orchestrator.
Before:
> - `DELETE /api/v1/proj/remove` for cleanup. Same tagging.
After:
> - `DELETE /api/v1/proj/{project_id}/remove` for cleanup — the project id is a path segment; the flat `/api/v1/proj/remove` is not a delete route. Same tagging.
Why: The cleanup instruction itself named a non-existent route, directly causing the undeleted fixtures.

### Change 4: Add a Round 2 mode section so targeted probers skip the full sweep
Observed failure: running the full flat-path protocol exhausted the budget in round 1 — items.md and write.md both hit calls=40 of 40 — leaving open questions unanswered; round 2 is a targeted question list (recon/unresolved.md), not a fresh full sweep.
Before:
> (no Round 2 mode section existed)
After:
> ## Round 2 mode
> If the dispatch prompt gives you a list of specific questions (round 2), answer exactly those, each as its own numbered attempt in the recording format below, and skip the full per-endpoint protocol above. The route shapes are already known: ids are path segments (`/api/v1/proj/{project_id}/...`, `/api/v1/proj/{project_id}/items/{todo_id}/...`), and cleanup is `DELETE /api/v1/proj/{project_id}/remove`. Do not re-sweep the flat paths or the field-name candidate lists — in round 1 that sweeping consumed whole 40-call budgets before the real routes were reached.
Why: Round-two probers must answer the dispatch's questions directly rather than re-run the full protocol that already exhausted the budget in round one.
