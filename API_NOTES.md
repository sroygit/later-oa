# Projects API notes (after round 1)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Generated from: recon/round1/read.md, recon/round1/write.md, recon/round1/remove.md, recon/round1/items.md

Citation form: `[<file>#<section> Attempt <n>]`. read.md, write.md and remove.md number attempts per endpoint section, so the section is included; items.md numbers attempts globally.

Route-shape note for readers of the brief: the brief lists every mutating/sub-resource route as a flat path (`/api/v1/proj/modify`, `/api/v1/proj/remove`, `/api/v1/proj/items/add`, ...). The real routes put the project id (and, for todo operations, the todo id) in the path. Each section below is headed with the brief's name and immediately states the real route. Mapping:

| Brief says | Real route (confirmed unless marked) |
|---|---|
| `GET /api/v1/proj/` | dead route, always 404 |
| `PUT /api/v1/proj/modify` | unknown; presumed `PUT /api/v1/proj/{project_id}/modify` (not yet called) |
| `POST /api/v1/proj/touch` | unknown; presumed `POST /api/v1/proj/{project_id}/touch` (not yet called) |
| `DELETE /api/v1/proj/remove` | `DELETE /api/v1/proj/{project_id}/remove` |
| `GET /api/v1/proj/items` | `GET /api/v1/proj/{project_id}/items` |
| `POST /api/v1/proj/items/add` | `POST /api/v1/proj/{project_id}/items/add` |
| `POST /api/v1/proj/items/mark` | `POST /api/v1/proj/{project_id}/items/{todo_id}/mark` |
| `DELETE /api/v1/proj/items/yank` | `DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank` |
| (not in brief) | `GET /api/v1/proj/{project_id}` single-project fetch |

## Confirmed behaviour

### GET /api/v1/health
- Purpose: liveness check.
- Accepts: nothing. [read.md#GET /api/v1/health Attempt 1]
- Returns: HTTP 200 `{"status":"ok"}` [read.md#GET /api/v1/health Attempt 1]
- Errors seen: HTTP 404 `{"error":"not found"}` on `/api/v1/health/` (trailing slash) [read.md#GET /api/v1/health Attempt 2]

### GET /api/v1/proj
- Purpose: paginated list of all projects, each with its embedded `items` array. No filtering.
- Accepts: query `from` (integer, optional, default 0, offset into the list) and `take` (integer, optional, default 5, effective maximum 5). [read.md#GET /api/v1/proj Attempt 1] [read.md#GET /api/v1/proj Attempt 2] [read.md#GET /api/v1/proj Attempt 3] [read.md#GET /api/v1/proj Attempt 4]
- Returns: HTTP 200 `{"from":<int>,"projects":[<project>...],"take":<int effective>,"total":<int>}`. `project` = `{"description":"","id":"proj_23315f","items":[<todo>...],"status":"wip","title":"Spring product launch","updated_at":1793577285470}`; `todo` = `{"by":1793750085470,"done":false,"id":"todo_9e5e55","task":"Finalize launch blog post","who":"betty"}`. [read.md#GET /api/v1/proj Attempt 1] [remove.md#GET /api/v1/proj Attempt 3]
- `take` semantics (reconciled): the read prober observed `take=2` returning 2 projects with `"take":2` echoed, `take=0` returning `[]` with `"take":0`, and `take=100` / `take=6` returning 5 with `"take":5` [read.md#GET /api/v1/proj Attempt 3] [read.md#GET /api/v1/proj Attempt 7] [read.md#GET /api/v1/proj Attempt 8] [read.md#GET /api/v1/proj Attempt 11]. The remove and write probers each tried only `take=20`, got 5 with `"take":5`, and wrote that `take` is "ignored" [remove.md#GET /api/v1/proj Attempt 2] [write.md#GET /api/v1/proj Attempt 2]. All six observations agree: `take` is honoured in the range 0..5 and clamped to 5 above that; the response echoes the clamped (effective) value, not the requested one. "Ignored" is not supported by the evidence; "capped at 5" is.
- `from` beyond the end returns an empty page with HTTP 200, and a negative `from` is accepted and also returns an empty page: `from=-1` gives `{"from":-1,"projects":[],"take":5,"total":13}`. [read.md#GET /api/v1/proj Attempt 10]
- Query params `id=` and `status=` are silently ignored; the default page comes back unchanged. [read.md#GET /api/v1/proj Attempt 5] [read.md#GET /api/v1/proj Attempt 6]
- Errors seen: HTTP 400 `{"error":"from/take must be integers"}` when `take=abc` (one message covers both params). [read.md#GET /api/v1/proj Attempt 9]
- OPTIONS: `Allow: GET, HEAD, OPTIONS`. [remove.md#DELETE /api/v1/proj/remove Attempt 8]

### GET /api/v1/proj/ (trailing slash, as listed in the brief)
- Purpose: none. It is a dead route.
- Returns: HTTP 404 `{"error":"not found"}` for every query-parameter variant tried (`id`, `project_id`, `pid`, `proj_id`, `projectId`, none). [read.md#GET /api/v1/proj/ Attempt 1] [read.md#GET /api/v1/proj/ Attempt 2] [read.md#GET /api/v1/proj/ Attempt 3] [read.md#GET /api/v1/proj/ Attempt 4] [read.md#GET /api/v1/proj/ Attempt 5] [read.md#GET /api/v1/proj/ Attempt 6]

### GET /api/v1/proj/{project_id} (not in brief; discovered)
- Purpose: fetch one project with its items.
- Accepts: project id as the path segment. No query params known. [read.md#GET /api/v1/proj/{id} Attempt 1]
- Returns: HTTP 200 with the same `project` shape as the list entries, e.g. `{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}`. [read.md#GET /api/v1/proj/{id} Attempt 1] [write.md#GET /api/v1/proj/<id> Attempt 1]
- Errors seen: HTTP 404 `{"error":"no such project"}` for an unknown id [read.md#GET /api/v1/proj/{id} Attempt 3]; HTTP 404 `{"error":"no such project"}` for an uppercased valid id (`PROJ_23315F`) [read.md#GET /api/v1/proj/{id} Attempt 4]; HTTP 404 `{"error":"not found"}` with a trailing slash [read.md#GET /api/v1/proj/{id} Attempt 2]; HTTP 405 `{"error":"method not allowed"}` on DELETE [remove.md#DELETE /api/v1/proj/remove Attempt 12] [write.md#DELETE /api/v1/proj/remove Attempt 6].
- OPTIONS: `Allow: GET, HEAD, OPTIONS`. [remove.md#DELETE /api/v1/proj/remove Attempt 7] [write.md#DELETE /api/v1/proj/remove Attempt 7]

### POST /api/v1/proj/new
- Purpose: create a project.
- Accepts: JSON body with `title` (required; any JSON type is stored verbatim, a number is not coerced to string) and `status` (optional, one of `blocked|dropped|kickoff|wip|wrapped`, exact lowercase, default `kickoff`). `description` was never sent; see Unresolved. [write.md#POST /api/v1/proj/new Attempt 2] [write.md#POST /api/v1/proj/new Attempt 3] [write.md#POST /api/v1/proj/new Attempt 7] [remove.md#POST /api/v1/proj/new Attempt 1] [items.md#Attempt 1]
- Returns: HTTP 201 with the full new project: `{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}`. [write.md#POST /api/v1/proj/new Attempt 2] [remove.md#POST /api/v1/proj/new Attempt 2] [items.md#Attempt 1]
- Errors seen: HTTP 400 `{"error":"title is required"}` with no body [write.md#POST /api/v1/proj/new Attempt 1]; HTTP 400 `{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}` for `active`, `Active`, and `WIP` [write.md#POST /api/v1/proj/new Attempt 5] [write.md#POST /api/v1/proj/new Attempt 6] [write.md#POST /api/v1/proj/new Attempt 8]; HTTP 404 `{"error":"not found"}` on `/api/v1/proj/new/` (trailing slash, nothing created) [write.md#POST /api/v1/proj/new Attempt 4].
- OPTIONS: `Allow: GET, POST, HEAD, OPTIONS` (the only path seen advertising POST). [remove.md#DELETE /api/v1/proj/remove Attempt 9]

### PUT /api/v1/proj/modify
- Status: NOT CONFIRMED. The flat path was never accepted; the nested form `PUT /api/v1/proj/{project_id}/modify` was never tried. Nothing is known about its accepted fields or response. See Unresolved (first group).
- Errors seen on the flat path: HTTP 405 `{"error":"method not allowed"}` for PUT (with and without body), POST, PATCH [write.md#PUT /api/v1/proj/modify Attempt 1] [write.md#PUT /api/v1/proj/modify Attempt 2] [write.md#PUT /api/v1/proj/modify Attempt 4] [write.md#PUT /api/v1/proj/modify Attempt 11]; OPTIONS `Allow: GET, HEAD, OPTIONS` [write.md#PUT /api/v1/proj/modify Attempt 3]; GET returns HTTP 404 `{"error":"no such project"}` regardless of `id`/`project_id`/`pid` query params or whether the id exists [write.md#PUT /api/v1/proj/modify Attempt 5] [write.md#PUT /api/v1/proj/modify Attempt 6] [write.md#PUT /api/v1/proj/modify Attempt 10]; `/modify/<id>` and `/modify/` return HTTP 404 `{"error":"not found"}` [write.md#PUT /api/v1/proj/modify Attempt 9] [write.md#PUT /api/v1/proj/modify Attempt 13]. These responses are exactly what `GET /api/v1/proj/{project_id}` produces with the literal id `modify`; they say nothing about how modify works.

### POST /api/v1/proj/touch
- Status: NOT CONFIRMED. Same situation as modify; the nested form `POST /api/v1/proj/{project_id}/touch` was never tried. No `updated_at` change was ever observed. See Unresolved (second group).
- Errors seen on the flat path: HTTP 405 `{"error":"method not allowed"}` for POST [write.md#POST /api/v1/proj/touch Attempt 1]; OPTIONS `Allow: GET, HEAD, OPTIONS` [write.md#POST /api/v1/proj/touch Attempt 2]; GET returns HTTP 404 `{"error":"no such project"}` with or without `?id=` [write.md#POST /api/v1/proj/touch Attempt 3] [write.md#POST /api/v1/proj/touch Attempt 4]; `/touch/<id>` and `/touch/` return HTTP 404 `{"error":"not found"}` [write.md#POST /api/v1/proj/touch Attempt 5] [write.md#POST /api/v1/proj/touch Attempt 6].

### DELETE /api/v1/proj/remove
- Real route: `DELETE /api/v1/proj/{project_id}/remove`.
- Purpose: delete a project.
- Accepts: project id as the path segment; no body, no query. [items.md#Attempt 40]
- Returns: HTTP 200 `{"removed":"proj_dc0698"}`. Deletion persists: the project vanished from the list and `total` dropped 13 to 12 in another prober's concurrent read. [items.md#Attempt 40] [write.md#GET /api/v1/proj Attempt 4]
- Errors seen on the flat path `/api/v1/proj/remove`: HTTP 405 `{"error":"method not allowed"}` for DELETE, POST, PUT, PATCH, with or without body, query id, form body, or `X-HTTP-Method-Override` [remove.md#DELETE /api/v1/proj/remove Attempt 1] [remove.md#DELETE /api/v1/proj/remove Attempt 2] [remove.md#DELETE /api/v1/proj/remove Attempt 4] [remove.md#DELETE /api/v1/proj/remove Attempt 5] [remove.md#DELETE /api/v1/proj/remove Attempt 13] [remove.md#DELETE /api/v1/proj/remove Attempt 14] [remove.md#DELETE /api/v1/proj/remove Attempt 15] [remove.md#DELETE /api/v1/proj/remove Attempt 16] [items.md#Attempt 38] [items.md#Attempt 39]; OPTIONS `Allow: GET, HEAD, OPTIONS` [remove.md#DELETE /api/v1/proj/remove Attempt 6] [write.md#DELETE /api/v1/proj/remove Attempt 3]; GET returns HTTP 404 `{"error":"no such project"}` [remove.md#DELETE /api/v1/proj/remove Attempt 3] [write.md#DELETE /api/v1/proj/remove Attempt 4]; `/remove/<id>` (id after the verb) is HTTP 404 `{"error":"not found"}` for OPTIONS and DELETE [remove.md#DELETE /api/v1/proj/remove Attempt 10] [remove.md#DELETE /api/v1/proj/remove Attempt 11]; `/remove/` is HTTP 404 `{"error":"not found"}` [remove.md#DELETE /api/v1/proj/remove Attempt 17].
- Not yet observed: removing an id that does not exist, and removing the same id twice (the brief's explicit ask for this slice). See Unresolved.

### GET /api/v1/proj/items
- Real route: `GET /api/v1/proj/{project_id}/items`.
- Purpose: list the todos of one project.
- Accepts: project id as the path segment. Query params, headers (`X-Project-Id`) and the flat path do not work. [items.md#Attempt 23] [items.md#Attempt 24]
- Returns: HTTP 200 `{"items":[<todo>...]}`, e.g. `{"items":[{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}]}`; `{"items":[]}` for a project with none. [items.md#Attempt 23] [items.md#Attempt 28] [items.md#Attempt 37]
- Errors seen: flat `GET /api/v1/proj/items` returns HTTP 404 `{"error":"no such project"}` for every query-param candidate (`id`, `project_id`, `pid`, `proj_id`, `projectId`, `title`, `name`) [items.md#Attempt 2] [items.md#Attempt 3] [items.md#Attempt 4] [items.md#Attempt 5] [items.md#Attempt 6] [items.md#Attempt 7] [items.md#Attempt 8] [items.md#Attempt 9]; flat `POST /api/v1/proj/items` returns HTTP 405 [items.md#Attempt 17] [items.md#Attempt 18].

### POST /api/v1/proj/items/add
- Real route: `POST /api/v1/proj/{project_id}/items/add`.
- Purpose: create a todo in a project.
- Accepts: JSON body with `task` (required), `who` (optional, default `""`), `by` (optional, default an epoch-ms integer near request time; a string such as `"2026-12-01"` is stored verbatim with no validation). [items.md#Attempt 25] [items.md#Attempt 26] [items.md#Attempt 27]
- Returns: HTTP 201 with the stored todo: `{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}`; the response equals what a later list returns. [items.md#Attempt 26] [items.md#Attempt 27] [items.md#Attempt 28]
- Errors seen: HTTP 400 `{"error":"task is required"}` with no body [items.md#Attempt 25]; the flat `/api/v1/proj/items/add` is HTTP 404 `{"error":"not found"}` for POST (any body), GET, PUT, and with a trailing slash [items.md#Attempt 10] [items.md#Attempt 11] [items.md#Attempt 12] [items.md#Attempt 14] [items.md#Attempt 15] [items.md#Attempt 16].

### POST /api/v1/proj/items/mark
- Real route: `POST /api/v1/proj/{project_id}/items/{todo_id}/mark`.
- Purpose: set a todo's `done` flag (explicit set, not a toggle).
- Accepts: both ids as path segments; JSON body `flag` (required, exactly the string `"yes"` or `"no"`). [items.md#Attempt 31] [items.md#Attempt 32] [items.md#Attempt 35]
- Returns: HTTP 200 with the updated todo, e.g. `{"by":1793578132540,"done":true,"id":"todo_fec6bd","task":"wash dishes","who":""}`. Repeating `"yes"` leaves `done:true`; `"no"` sets `done:false`. Change persists in the list. [items.md#Attempt 32] [items.md#Attempt 33] [items.md#Attempt 34] [items.md#Attempt 35]
- Errors seen: HTTP 400 `{"error":"flag must be 'yes' or 'no'"}` with no body [items.md#Attempt 31]; flat `/api/v1/proj/items/mark` is HTTP 404 `{"error":"not found"}` [items.md#Attempt 19] [items.md#Attempt 21]; `/api/v1/proj/{project_id}/items/mark` (todo id in body instead of path) is HTTP 404 `{"error":"not found"}` [items.md#Attempt 29] [items.md#Attempt 30].

### DELETE /api/v1/proj/items/yank
- Real route: `DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank`.
- Purpose: delete one todo.
- Accepts: both ids as path segments; no body. [items.md#Attempt 36]
- Returns: HTTP 200 `{"removed":"todo_bedcfc"}`; only the targeted todo disappears from the list. [items.md#Attempt 36] [items.md#Attempt 37]
- Errors seen: flat `/api/v1/proj/items/yank` is HTTP 404 `{"error":"not found"}` for DELETE and GET. [items.md#Attempt 20] [items.md#Attempt 22]

### Identifiers and formats
- Project id: `proj_` + 6 lowercase hex chars, e.g. `proj_aa6cb4`; server-generated; case-sensitive on lookup. [write.md#POST /api/v1/proj/new Attempt 2] [remove.md#POST /api/v1/proj/new Attempt 1] [read.md#GET /api/v1/proj/{id} Attempt 4]
- Todo id: `todo_` + 6 lowercase hex chars, e.g. `todo_fec6bd`; server-generated. [items.md#Attempt 26]
- Dates: `updated_at` (project) and `by` (todo) are Unix epoch milliseconds as JSON integers, e.g. `1793578023313`; but `by` is stored as whatever the client sends, so a string `"2026-12-01"` can appear in the same field. [write.md#POST /api/v1/proj/new Attempt 2] [read.md#GET /api/v1/proj Attempt 1] [items.md#Attempt 27]
- Status values seen: exactly `blocked`, `dropped`, `kickoff`, `wip`, `wrapped` (from the server's own validation message); all five appear in the seed data; default on create is `kickoff`. [write.md#POST /api/v1/proj/new Attempt 5] [read.md#GET /api/v1/proj Attempt 1] [read.md#GET /api/v1/proj Attempt 2] [write.md#POST /api/v1/proj/new Attempt 2]
- Project shape: `description` (string, default `""`), `id`, `items` (array of todo, default `[]`), `status`, `title` (usually string; see Quirks), `updated_at`. [write.md#POST /api/v1/proj/new Attempt 2]
- Todo shape: `by`, `done` (boolean, default `false`), `id`, `task`, `who` (string, default `""`). [items.md#Attempt 26]
- Error body: always `{"error":"<message>"}`. Two different 404 messages: `"not found"` = no route matched; `"no such project"` = a route matched but the project lookup failed. [read.md#GET /api/v1/proj/{id} Attempt 2] [read.md#GET /api/v1/proj/{id} Attempt 3]
- Pagination defaults: `from=0`, `take=5`, page size ceiling 5. [read.md#GET /api/v1/proj Attempt 1] [read.md#GET /api/v1/proj Attempt 11]
- Seed data: 7 projects pre-exist (`proj_23315f`, `proj_756702`, `proj_ad713f`, `proj_338616`, `proj_e869bb`, `proj_828748`, `proj_bd0d1e`); do not modify or delete them. [read.md#GET /api/v1/proj Attempt 1] [read.md#GET /api/v1/proj Attempt 2]

## Quirks
- The flat paths from the brief (`/api/v1/proj/modify`, `/touch`, `/remove`, `/items`) are swallowed by the `GET /api/v1/proj/{project_id}` route with the literal word as the id: GET gives 404 `no such project`, every other verb gives 405, and OPTIONS advertises only `GET, HEAD, OPTIONS`. These 405s mean "wrong path", not "wrong verb". [write.md#PUT /api/v1/proj/modify Attempt 3] [write.md#PUT /api/v1/proj/modify Attempt 5] [remove.md#DELETE /api/v1/proj/remove Attempt 3] [remove.md#DELETE /api/v1/proj/remove Attempt 7] [items.md#Attempt 2] [items.md#Attempt 17]
- The real mutating routes nest ids as path segments (`/proj/{pid}/remove`, `/proj/{pid}/items/add`, `/proj/{pid}/items/{tid}/mark`), even though the id-less literal path for the sibling `/proj/new` is a real route. [items.md#Attempt 25] [items.md#Attempt 31] [items.md#Attempt 40] [remove.md#DELETE /api/v1/proj/remove Attempt 9]
- OPTIONS on `/api/v1/proj/{id}` says `Allow: GET, HEAD, OPTIONS`, yet `DELETE /api/v1/proj/{id}/remove` and `POST /api/v1/proj/{id}/items/add` work. Allow headers describe only the exact path and cannot be used to discover sub-routes. [remove.md#DELETE /api/v1/proj/remove Attempt 7] [items.md#Attempt 40]
- `DELETE /api/v1/proj/{id}` (REST style) is 405; deletion requires the `/remove` suffix. [remove.md#DELETE /api/v1/proj/remove Attempt 12] [items.md#Attempt 40]
- Three distinct failure signals: 404 `not found` (no route), 405 `method not allowed` (route exists, verb rejected before body is read), 404 `no such project` (handler ran, lookup failed). [items.md#Attempt 13] [items.md#Attempt 16] [items.md#Attempt 17] [read.md#GET /api/v1/proj/{id} Attempt 3]
- Trailing slashes are never normalized; every path tried with one returned 404 `not found`, including on routes that otherwise work and on `/new` with a valid body (nothing created). [read.md#GET /api/v1/health Attempt 2] [read.md#GET /api/v1/proj/ Attempt 1] [read.md#GET /api/v1/proj/{id} Attempt 2] [write.md#POST /api/v1/proj/new Attempt 4] [remove.md#DELETE /api/v1/proj/remove Attempt 17] [write.md#PUT /api/v1/proj/modify Attempt 13] [write.md#POST /api/v1/proj/touch Attempt 6]
- `take` above 5 is silently clamped and the response echoes the clamped value (`take=100` returns `"take":5`), so a client cannot detect the clamp from the echo alone. [read.md#GET /api/v1/proj Attempt 8] [read.md#GET /api/v1/proj Attempt 11]
- `take=0` is accepted (empty page) and `from=-1` returns 200 with an empty page instead of 400, while `take=abc` is a 400. [read.md#GET /api/v1/proj Attempt 7] [read.md#GET /api/v1/proj Attempt 10] [read.md#GET /api/v1/proj Attempt 9]
- `id` and `status` query params on the list endpoint are silently ignored rather than rejected. [read.md#GET /api/v1/proj Attempt 5] [read.md#GET /api/v1/proj Attempt 6]
- `title` is not type-checked: `{"title":12345}` is stored and returned as the JSON number `12345`, so project titles in the list are not guaranteed to be strings. [write.md#POST /api/v1/proj/new Attempt 3] [remove.md#GET /api/v1/proj Attempt 4]
- `status` enum is case-sensitive lowercase, and the error message renders the set in Python list syntax (`['blocked', 'dropped', ...]`). [write.md#POST /api/v1/proj/new Attempt 8] [write.md#POST /api/v1/proj/new Attempt 5]
- Todo field names are terse and non-obvious: `task` (not text/title), `who` (assignee), `by` (due), `flag` (for mark), and the delete verb is `yank`. [items.md#Attempt 25] [items.md#Attempt 26] [items.md#Attempt 31] [items.md#Attempt 36]
- `mark` wants `flag: "yes"|"no"` strings, not a boolean, and writes the result to a field called `done`. [items.md#Attempt 31] [items.md#Attempt 32]
- `by` (todo due) defaults to an epoch-ms value near request time rather than null, and accepts any JSON value verbatim (a date string is stored as a string). Readers must handle both number and string. [items.md#Attempt 26] [items.md#Attempt 27]
- `who` defaults to `""`, not null or absent. [items.md#Attempt 26]
- Project ids are case-sensitive (`PROJ_23315F` is `no such project`). [read.md#GET /api/v1/proj/{id} Attempt 4]
- Sending a JSON body on GET produced an HTTP/2 stream error at the client (curl exit 92), not an API response. Do not send bodies on GET. [write.md#PUT /api/v1/proj/modify Attempt 12]
- `total` in the list is live, not a snapshot: it moved 10 to 13 during one prober's session while others created fixtures. [read.md#GET /api/v1/proj Attempt 1] [read.md#GET /api/v1/proj Attempt 11]

## Unresolved
- Create a fixture with POST /api/v1/proj/new `{"title":"r2-modify-1"}`, then PUT /api/v1/proj/{id}/modify with JSON `{"title":"r2-modify-1-renamed"}`. Record status, body, and whether GET /api/v1/proj/{id} shows the new title and a changed `updated_at`.
- If that PUT is 405, send OPTIONS /api/v1/proj/{id}/modify and record the Allow header; then try POST and PATCH /api/v1/proj/{id}/modify with the same body and record which succeeds.
- PUT /api/v1/proj/{id}/modify with `{"status":"wrapped"}`, then with `{"status":"WIP"}`. Record whether status changes and whether the same case-sensitive enum error from /new appears.
- PUT /api/v1/proj/{id}/modify with `{"description":"r2 description"}`. Record whether `description` is updatable.
- PUT /api/v1/proj/{id}/modify with `{}`. Record whether a 400 names required fields or a 200 returns the project unchanged.
- PUT /api/v1/proj/{id}/modify with `{"id":"proj_23315f","title":"should-not-apply"}`. Record whether a body `id` is ignored or overrides the path id (check GET on both ids afterwards).
- PUT /api/v1/proj/does_not_exist/modify with `{"title":"x"}`. Record status and body.
- PUT /api/v1/proj/{id}/modify with `{"items":[]}` on a project that has one todo. Record whether items can be wiped through modify.
- GET /api/v1/proj/{id} and note `updated_at`; wait at least 1 second; POST /api/v1/proj/{id}/touch with no body. Record status, body, and whether `updated_at` increased on a following GET.
- If that POST is 405, send OPTIONS /api/v1/proj/{id}/touch and record the Allow header; then try PUT and PATCH on the same path.
- POST /api/v1/proj/{id}/touch with JSON `{"status":"wip","title":"touched"}`. Record whether touch applies any fields or ignores the body.
- POST /api/v1/proj/does_not_exist/touch. Record status and body.
- Create a fixture, DELETE /api/v1/proj/{id}/remove and record the 200 body; then DELETE the same path again. Record status and body of the second call.
- DELETE /api/v1/proj/does_not_exist/remove. Record status and body.
- DELETE /api/v1/proj/{id}/remove/ (trailing slash) on a live fixture. Record status and whether the fixture survived.
- OPTIONS /api/v1/proj/{id}/remove and record the Allow header; then POST /api/v1/proj/{id}/remove and record whether POST also deletes.
- After a successful remove, GET /api/v1/proj/{id} and GET /api/v1/proj?from=0. Record that the first is 404 `no such project` and `total` dropped by one.
- POST /api/v1/proj/new with `{"title":"r2-desc","description":"hello"}`. Record whether `description` is stored.
- POST /api/v1/proj/new with `{"title":""}`. Record 400 vs 201.
- POST /api/v1/proj/new with `{"title":"r2-inline","items":[{"task":"t"}]}`. Record whether items can be created inline or are ignored.
- POST /api/v1/proj/new with `{"title":"r2-ids","id":"proj_custom","updated_at":1}`. Record whether server-controlled fields are ignored or echoed.
- POST /api/v1/proj/new with `Content-Type: application/x-www-form-urlencoded` body `title=r2-form`. Record whether form bodies are accepted.
- GET /api/v1/proj?take=5 and GET /api/v1/proj?take=4. Record the project count and echoed `take` to pin the ceiling at exactly 5.
- GET /api/v1/proj?from=-5 and GET /api/v1/proj?from=999. Record status, echoed `from`, and project count.
- GET /api/v1/proj?from=1.5 and GET /api/v1/proj?take=-1. Record status and message.
- GET /api/v1/proj?from=0&take=5 then ?from=5&take=5 then ?from=10&take=5 and record whether order is stable creation order (compare `updated_at` sequence across pages).
- GET /api/v1/proj/proj_23315f?take=1&status=wip. Record whether query params are ignored on the single-project route.
- PUT /api/v1/proj/{id} and PATCH /api/v1/proj/{id} with `{"title":"x"}`. Record 405 vs anything else.
- GET /api/v1/proj/does_not_exist/items. Record status and body.
- GET /api/v1/proj/{id}/items/ (trailing slash). Record status and body.
- GET /api/v1/proj/{id}/items?from=0&take=1 on a project with 2 or more todos. Record whether the items list paginates.
- POST /api/v1/proj/does_not_exist/items/add with `{"task":"x"}`. Record status and body.
- POST /api/v1/proj/{id}/items/add with `{"task":"x","by":"not-a-date"}`, then `{"task":"x","by":-1}`, then `{"task":"x","who":123}`. Record which, if any, are rejected.
- POST /api/v1/proj/{id}/items/add with `{"task":"x","done":true}`. Record whether `done` can be set at creation.
- POST /api/v1/proj/{id}/items/add with `{"task":""}` and `{"task":123}`. Record status and body.
- GET /api/v1/proj/{id}, add a todo, GET /api/v1/proj/{id} again. Record whether the project's `updated_at` changed and whether the project's `items` array includes the new todo.
- POST /api/v1/proj/{id}/items/{tid}/mark with `{"flag":"Yes"}`, `{"flag":true}`, `{"flag":"true"}`, `{"flag":1}`. Record which are 400 and the exact message.
- POST /api/v1/proj/{id}/items/todo_bogus/mark with `{"flag":"yes"}`. Record status and body.
- POST /api/v1/proj/{other_id}/items/{tid}/mark with `{"flag":"yes"}` where `tid` belongs to a different project. Record whether the project scope is enforced.
- Mark a todo and GET /api/v1/proj/{id} before and after. Record whether the project's `updated_at` changes.
- DELETE /api/v1/proj/{id}/items/{tid}/yank twice. Record status and body of the second call.
- DELETE /api/v1/proj/{id}/items/todo_bogus/yank. Record status and body.
- DELETE /api/v1/proj/{other_id}/items/{tid}/yank where `tid` belongs to a different project. Record whether it is refused.
- Yank a todo and GET /api/v1/proj/{id} before and after. Record whether the project's `updated_at` changes.
