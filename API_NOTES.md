# Projects API notes (after round 2)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Generated from: recon/round1/read.md, recon/round1/write.md, recon/round1/remove.md, recon/round1/items.md, recon/round2/modify-touch.md, recon/round2/items.md, recon/round2/lifecycle.md

Citation form: `[round<N>/<file>#<section> Attempt <n>]`. Every findings file except round1/items.md numbers attempts per endpoint section, so the section is named by its action word: `health`, `list` (GET /api/v1/proj), `list-slash` (GET /api/v1/proj/), `get-id` (GET /api/v1/proj/{id}), `new`, `modify`, `touch`, `remove`, `items`, `add`, `mark`, `yank`. round1/items.md numbers attempts globally and is cited as `[round1/items.md#Attempt <n>]`.

Route-shape note for readers of the brief: the brief lists every mutating/sub-resource route as a flat path (`/api/v1/proj/modify`, `/api/v1/proj/remove`, `/api/v1/proj/items/add`, ...). The real routes put the project id (and, for todo operations, the todo id) in the path. Each section below is headed with the brief's name and immediately states the real route. Mapping:

| Brief says | Real route (all confirmed) |
|---|---|
| `GET /api/v1/proj/` | dead route, always 404 |
| `PUT /api/v1/proj/modify` | `PUT /api/v1/proj/{project_id}/modify` |
| `POST /api/v1/proj/touch` | `POST /api/v1/proj/{project_id}/touch` |
| `DELETE /api/v1/proj/remove` | `DELETE /api/v1/proj/{project_id}/remove` |
| `GET /api/v1/proj/items` | `GET /api/v1/proj/{project_id}/items` |
| `POST /api/v1/proj/items/add` | `POST /api/v1/proj/{project_id}/items/add` |
| `POST /api/v1/proj/items/mark` | `POST /api/v1/proj/{project_id}/items/{todo_id}/mark` |
| `DELETE /api/v1/proj/items/yank` | `DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank` |
| (not in brief) | `GET /api/v1/proj/{project_id}` single-project fetch |

The one rule a client must know before anything else: a project's `updated_at` is set at creation and changed by exactly one call, `POST /api/v1/proj/{project_id}/touch`. Editing the project (modify) or its todos (add, mark, yank) leaves it frozen. See Quirks.

## Confirmed behaviour

### GET /api/v1/health
- Purpose: liveness check.
- Accepts: nothing. [round1/read.md#health Attempt 1]
- Returns: HTTP 200 `{"status":"ok"}` [round1/read.md#health Attempt 1]
- Errors seen: HTTP 404 `{"error":"not found"}` on `/api/v1/health/` (trailing slash) [round1/read.md#health Attempt 2]

### GET /api/v1/proj
- Purpose: paginated list of all projects, each with its embedded `items` array. No filtering.
- Accepts: query `from` (integer, optional, default 0, offset into the list) and `take` (integer, optional, default 5, maximum 5). [round1/read.md#list Attempt 1] [round1/read.md#list Attempt 2] [round1/read.md#list Attempt 3] [round1/read.md#list Attempt 4]
- Returns: HTTP 200 `{"from":<int>,"projects":[<project>...],"take":<int effective>,"total":<int>}`. `project` = `{"description":"","id":"proj_23315f","items":[<todo>...],"status":"wip","title":"Spring product launch","updated_at":1793577285470}`; `todo` = `{"by":1793750085470,"done":false,"id":"todo_9e5e55","task":"Finalize launch blog post","who":"betty"}`. [round1/read.md#list Attempt 1] [round1/remove.md#list Attempt 3]
- `take` ceiling pinned at exactly 5: `take=4` returns 4 projects with `"take":4`, `take=5` returns 5 with `"take":5`, `take=6` and `take=100` return 5 with `"take":5`. The response echoes the effective (clamped) value, not the requested one. `take` changes the page size only; `total` is the same for `take=4` and `take=5`. [round2/lifecycle.md#list Attempt 1] [round2/lifecycle.md#list Attempt 2] [round1/read.md#list Attempt 3] [round1/read.md#list Attempt 8] [round1/read.md#list Attempt 11]
- `total` is the live count of projects: it drops by exactly one after a successful remove. [round2/lifecycle.md#remove Attempt 13] [round2/lifecycle.md#remove Attempt 16] [round1/write.md#list Attempt 4]
- `from` beyond the end returns an empty page with HTTP 200, and a negative `from` is accepted and also returns an empty page: `from=-1` gives `{"from":-1,"projects":[],"take":5,"total":13}`. [round1/read.md#list Attempt 10]
- Query params `id=` and `status=` are silently ignored; the default page comes back unchanged. [round1/read.md#list Attempt 5] [round1/read.md#list Attempt 6]
- Errors seen: HTTP 400 `{"error":"from/take must be integers"}` when `take=abc` (one message covers both params). [round1/read.md#list Attempt 9]
- OPTIONS: `Allow: GET, HEAD, OPTIONS`. [round1/remove.md#remove Attempt 8]

### GET /api/v1/proj/ (trailing slash, as listed in the brief)
- Purpose: none. It is a dead route.
- Returns: HTTP 404 `{"error":"not found"}` for every query-parameter variant tried (`id`, `project_id`, `pid`, `proj_id`, `projectId`, none). [round1/read.md#list-slash Attempt 1] [round1/read.md#list-slash Attempt 2] [round1/read.md#list-slash Attempt 3] [round1/read.md#list-slash Attempt 4] [round1/read.md#list-slash Attempt 5] [round1/read.md#list-slash Attempt 6]

### GET /api/v1/proj/{project_id} (not in brief; discovered)
- Purpose: fetch one project with its items. This is the read a client should use after any mutation; its `items` array reflects add, mark and yank immediately, and showed 5 todos without truncation. [round2/items.md#add Attempt 7] [round2/items.md#mark Attempt 9] [round2/items.md#yank Attempt 6]
- Accepts: project id as the path segment. No query params known. [round1/read.md#get-id Attempt 1]
- Returns: HTTP 200 with the same `project` shape as the list entries, e.g. `{"description":"","id":"proj_aa6cb4","items":[],"status":"kickoff","title":"write-probe-1","updated_at":1793578023313}`. [round1/read.md#get-id Attempt 1] [round1/write.md#get-id Attempt 1] [round2/lifecycle.md#new Attempt 2]
- Errors seen: HTTP 404 `{"error":"no such project"}` for an unknown id [round1/read.md#get-id Attempt 3] and for an id that has been removed [round2/lifecycle.md#remove Attempt 15]; HTTP 404 `{"error":"no such project"}` for an uppercased valid id (`PROJ_23315F`) [round1/read.md#get-id Attempt 4]; HTTP 404 `{"error":"not found"}` with a trailing slash [round1/read.md#get-id Attempt 2]; HTTP 405 `{"error":"method not allowed"}` on DELETE [round1/remove.md#remove Attempt 12] [round1/write.md#remove Attempt 6], PUT and PATCH (JSON `{"title":"x"}`) [round2/lifecycle.md#get-id Attempt 2] [round2/lifecycle.md#get-id Attempt 3]. There is no in-place update on this path; use `/modify`.
- OPTIONS: `Allow: GET, HEAD, OPTIONS`. [round1/remove.md#remove Attempt 7] [round1/write.md#remove Attempt 7]

### POST /api/v1/proj/new
- Purpose: create a project.
- Accepts: JSON body with `title` (required, must be non-empty; any JSON type is stored verbatim, a number is not coerced to string), `status` (optional, one of `blocked|dropped|kickoff|wip|wrapped`, exact lowercase, default `kickoff`), `description` (optional string, default `""`). [round1/write.md#new Attempt 2] [round1/write.md#new Attempt 3] [round1/write.md#new Attempt 7] [round2/lifecycle.md#new Attempt 1] [round2/lifecycle.md#new Attempt 2] [round1/remove.md#new Attempt 1] [round1/items.md#Attempt 1]
- Returns: HTTP 201 with the full new project: `{"description":"hello","id":"proj_b4460a","items":[],"status":"kickoff","title":"r2-lifecycle-desc","updated_at":1793579023819}`. [round1/write.md#new Attempt 2] [round2/lifecycle.md#new Attempt 1] [round2/items.md#new Attempt 1]
- Errors seen: HTTP 400 `{"error":"title is required"}` with no body [round1/write.md#new Attempt 1] and with `{"title":""}` (nothing created) [round2/lifecycle.md#new Attempt 3]; HTTP 400 `{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}` for `active`, `Active`, and `WIP` [round1/write.md#new Attempt 5] [round1/write.md#new Attempt 6] [round1/write.md#new Attempt 8]; HTTP 404 `{"error":"not found"}` on `/api/v1/proj/new/` (trailing slash, nothing created) [round1/write.md#new Attempt 4].
- OPTIONS: `Allow: GET, POST, HEAD, OPTIONS`. [round1/remove.md#remove Attempt 9]

### PUT /api/v1/proj/modify
- Real route: `PUT /api/v1/proj/{project_id}/modify`. PUT works directly (no 405). [round2/modify-touch.md#modify Attempt 1]
- Purpose: partial update of a project's own fields. Does not touch `updated_at`.
- Accepts: project id as the path segment; JSON body with any subset of `title` (any JSON value), `status` (same enum as `/new`, exact lowercase), `description` (string). Every field is optional; `{}` is accepted. `items` in the body is silently ignored. [round2/modify-touch.md#modify Attempt 1] [round2/modify-touch.md#modify Attempt 3] [round2/modify-touch.md#modify Attempt 6] [round2/modify-touch.md#modify Attempt 8] [round2/modify-touch.md#modify Attempt 12]
- Returns: HTTP 200 with the full updated project, e.g. `{"description":"r2 description","id":"proj_72c717","items":[],"status":"wrapped","title":"r2-modify-touch-1-renamed","updated_at":1793579008014}`. Changes persist on a following GET. `updated_at` is the creation value, unchanged after four successful modifies. [round2/modify-touch.md#modify Attempt 1] [round2/modify-touch.md#modify Attempt 2] [round2/modify-touch.md#modify Attempt 5] [round2/modify-touch.md#modify Attempt 7] [round2/modify-touch.md#modify Attempt 13]
- With `{}`: HTTP 200, project returned unchanged, no 400. [round2/modify-touch.md#modify Attempt 8]
- With `{"items":[]}` on a project holding one todo: HTTP 200, the todo is still there. [round2/modify-touch.md#modify Attempt 12] [round2/modify-touch.md#modify Attempt 13]
- Errors seen: HTTP 400 `{"error":"status must be one of: ['blocked', 'dropped', 'kickoff', 'wip', 'wrapped']"}` for `"WIP"`, and the rejected call leaves status untouched [round2/modify-touch.md#modify Attempt 4] [round2/modify-touch.md#modify Attempt 5]; HTTP 404 `{"error":"no such project"}` for `/api/v1/proj/does_not_exist/modify` [round2/modify-touch.md#modify Attempt 9].
- Flat path `/api/v1/proj/modify` (the brief's spelling) is not this route: HTTP 405 for PUT/POST/PATCH, HTTP 404 `no such project` for GET with any query params, HTTP 404 `not found` for `/modify/<id>` and `/modify/`. [round1/write.md#modify Attempt 1] [round1/write.md#modify Attempt 4] [round1/write.md#modify Attempt 11] [round1/write.md#modify Attempt 6] [round1/write.md#modify Attempt 9] [round1/write.md#modify Attempt 13]

### POST /api/v1/proj/touch
- Real route: `POST /api/v1/proj/{project_id}/touch`. POST works directly (no 405). [round2/modify-touch.md#touch Attempt 1]
- Purpose: bump the project's `updated_at` to now. That is its only effect.
- Accepts: project id as the path segment; no body needed. A JSON body is accepted and completely ignored (`{"status":"wip","title":"touched"}` changed neither field). [round2/modify-touch.md#touch Attempt 1] [round2/modify-touch.md#touch Attempt 3]
- Returns: HTTP 200 with the full project and a new `updated_at`: 1793579008014 became 1793579049851 on the first touch and 1793579056134 on the second; the new value persists on a following GET. [round2/modify-touch.md#touch Attempt 1] [round2/modify-touch.md#touch Attempt 2] [round2/modify-touch.md#touch Attempt 3]
- Errors seen: HTTP 404 `{"error":"no such project"}` for `/api/v1/proj/does_not_exist/touch`. [round2/modify-touch.md#touch Attempt 4]
- Flat path `/api/v1/proj/touch` is not this route: HTTP 405 for POST, HTTP 404 `no such project` for GET with or without `?id=`, HTTP 404 `not found` for `/touch/<id>` and `/touch/`. [round1/write.md#touch Attempt 1] [round1/write.md#touch Attempt 3] [round1/write.md#touch Attempt 4] [round1/write.md#touch Attempt 5] [round1/write.md#touch Attempt 6]

### DELETE /api/v1/proj/remove
- Real route: `DELETE /api/v1/proj/{project_id}/remove`.
- Purpose: delete a project and its todos.
- Accepts: project id as the path segment; no body, no query. [round1/items.md#Attempt 40] [round2/lifecycle.md#remove Attempt 2]
- Returns: HTTP 200 `{"removed":"proj_3cf951"}`. Afterwards GET on the id is HTTP 404 `no such project` and the list's `total` drops by one. [round2/lifecycle.md#remove Attempt 2] [round2/lifecycle.md#remove Attempt 14] [round2/lifecycle.md#remove Attempt 15] [round2/lifecycle.md#remove Attempt 16] [round1/items.md#Attempt 40] [round1/write.md#list Attempt 4]
- Not idempotent: a second DELETE on the same id is HTTP 404 `{"error":"no such project"}`, byte-identical to deleting an id that never existed. [round2/lifecycle.md#remove Attempt 3] [round2/lifecycle.md#remove Attempt 4]
- OPTIONS on the nested path: `Allow: DELETE, OPTIONS`. [round2/lifecycle.md#remove Attempt 8]
- Errors seen: HTTP 404 `{"error":"no such project"}` for an unknown or already-removed id [round2/lifecycle.md#remove Attempt 3] [round2/lifecycle.md#remove Attempt 4]; HTTP 405 `{"error":"method not allowed"}` for POST on the nested path, project untouched [round2/lifecycle.md#remove Attempt 9] [round2/lifecycle.md#remove Attempt 10]; HTTP 404 `{"error":"not found"}` for `/api/v1/proj/{id}/remove/` (trailing slash), project survives [round2/lifecycle.md#remove Attempt 6] [round2/lifecycle.md#remove Attempt 7].
- Flat path `/api/v1/proj/remove` is not this route: HTTP 405 for DELETE, POST, PUT, PATCH with or without body, query id, form body, or `X-HTTP-Method-Override` [round1/remove.md#remove Attempt 1] [round1/remove.md#remove Attempt 2] [round1/remove.md#remove Attempt 4] [round1/remove.md#remove Attempt 5] [round1/remove.md#remove Attempt 13] [round1/remove.md#remove Attempt 14] [round1/remove.md#remove Attempt 15] [round1/remove.md#remove Attempt 16] [round1/items.md#Attempt 38] [round1/items.md#Attempt 39]; GET is HTTP 404 `no such project` [round1/remove.md#remove Attempt 3]; `/remove/<id>` (id after the verb) is HTTP 404 `not found` [round1/remove.md#remove Attempt 10] [round1/remove.md#remove Attempt 11].

### GET /api/v1/proj/items
- Real route: `GET /api/v1/proj/{project_id}/items`.
- Purpose: list the todos of one project.
- Accepts: project id as the path segment. Query params, headers (`X-Project-Id`) and the flat path do not work. [round1/items.md#Attempt 23] [round1/items.md#Attempt 24]
- Returns: HTTP 200 `{"items":[<todo>...]}`, e.g. `{"items":[{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}]}`; `{"items":[]}` for a project with none. [round1/items.md#Attempt 23] [round1/items.md#Attempt 28] [round1/items.md#Attempt 37]
- Errors seen: HTTP 404 `{"error":"no such project"}` for `/api/v1/proj/does_not_exist/items` [round2/items.md#items Attempt 1]; flat `GET /api/v1/proj/items` returns HTTP 404 `{"error":"no such project"}` for every query-param candidate [round1/items.md#Attempt 2] [round1/items.md#Attempt 3] [round1/items.md#Attempt 9]; flat `POST /api/v1/proj/items` returns HTTP 405 [round1/items.md#Attempt 17] [round1/items.md#Attempt 18].

### POST /api/v1/proj/items/add
- Real route: `POST /api/v1/proj/{project_id}/items/add`.
- Purpose: create a todo in a project. Does not touch the project's `updated_at`.
- Accepts: JSON body with `task` (required), `who` (optional, default `""`, any JSON value stored verbatim: `123` stays a number), `by` (optional, default an epoch-ms integer at request time; any JSON value stored verbatim: `"2026-12-01"`, `"not-a-date"` and `-1` were all accepted). `done` in the body is ignored; the todo is always created with `done:false`. [round1/items.md#Attempt 25] [round1/items.md#Attempt 26] [round1/items.md#Attempt 27] [round2/items.md#add Attempt 1] [round2/items.md#add Attempt 2] [round2/items.md#add Attempt 3] [round2/items.md#add Attempt 4]
- Returns: HTTP 201 with the stored todo: `{"by":1793578132540,"done":false,"id":"todo_fec6bd","task":"wash dishes","who":""}`; the response equals what a later list or project GET returns. [round1/items.md#Attempt 26] [round1/items.md#Attempt 28] [round2/items.md#add Attempt 6] [round2/items.md#add Attempt 7]
- Project `updated_at` is unchanged after an add (1793579030135 before and after). [round2/items.md#add Attempt 5] [round2/items.md#add Attempt 7] [round2/modify-touch.md#modify Attempt 11]
- Errors seen: HTTP 400 `{"error":"task is required"}` with no body [round1/items.md#Attempt 25]; the flat `/api/v1/proj/items/add` is HTTP 404 `{"error":"not found"}` for POST (any body), GET, PUT, and with a trailing slash [round1/items.md#Attempt 10] [round1/items.md#Attempt 11] [round1/items.md#Attempt 14] [round1/items.md#Attempt 15] [round1/items.md#Attempt 16].

### POST /api/v1/proj/items/mark
- Real route: `POST /api/v1/proj/{project_id}/items/{todo_id}/mark`.
- Purpose: set a todo's `done` flag (explicit set, not a toggle). Does not touch the project's `updated_at`.
- Accepts: both ids as path segments; JSON body `flag` (required, exactly the string `"yes"` or `"no"`). [round1/items.md#Attempt 31] [round1/items.md#Attempt 32] [round1/items.md#Attempt 35] [round2/items.md#mark Attempt 8]
- Returns: HTTP 200 with the updated todo, e.g. `{"by":1793578132540,"done":true,"id":"todo_fec6bd","task":"wash dishes","who":""}`. Repeating `"yes"` leaves `done:true`; `"no"` sets `done:false`. Change persists on the list and on the project GET. [round1/items.md#Attempt 32] [round1/items.md#Attempt 33] [round1/items.md#Attempt 34] [round1/items.md#Attempt 35] [round2/items.md#mark Attempt 9]
- Scope: the todo must belong to the project in the path. A valid todo id under another project's path is HTTP 404 `no such item`. [round2/items.md#mark Attempt 6]
- Project `updated_at` is unchanged after a mark. [round2/items.md#mark Attempt 7] [round2/items.md#mark Attempt 9]
- Errors seen: HTTP 400 `{"error":"flag must be 'yes' or 'no'"}` with no body and for `"Yes"`, `true`, `"true"`, `1` [round1/items.md#Attempt 31] [round2/items.md#mark Attempt 1] [round2/items.md#mark Attempt 2] [round2/items.md#mark Attempt 3] [round2/items.md#mark Attempt 4]; HTTP 404 `{"error":"no such item"}` for an unknown todo id [round2/items.md#mark Attempt 5]; flat `/api/v1/proj/items/mark` is HTTP 404 `{"error":"not found"}` [round1/items.md#Attempt 19] [round1/items.md#Attempt 21]; `/api/v1/proj/{project_id}/items/mark` (todo id in body instead of path) is HTTP 404 `{"error":"not found"}` [round1/items.md#Attempt 29] [round1/items.md#Attempt 30].

### DELETE /api/v1/proj/items/yank
- Real route: `DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank`.
- Purpose: delete one todo. Does not touch the project's `updated_at`.
- Accepts: both ids as path segments; no body. [round1/items.md#Attempt 36] [round2/items.md#yank Attempt 1]
- Returns: HTTP 200 `{"removed":"todo_bedcfc"}`; only the targeted todo disappears from the list and from the project GET. [round1/items.md#Attempt 36] [round1/items.md#Attempt 37] [round2/items.md#yank Attempt 5] [round2/items.md#yank Attempt 6]
- Not idempotent: a second yank of the same todo is HTTP 404 `{"error":"no such item"}`. [round2/items.md#yank Attempt 2]
- Scope: a valid todo id under another project's path is HTTP 404 `no such item`. [round2/items.md#yank Attempt 3]
- Project `updated_at` is unchanged after a yank. [round2/items.md#yank Attempt 4] [round2/items.md#yank Attempt 6]
- Errors seen: HTTP 404 `{"error":"no such item"}` for a todo not in this project (removed or foreign) [round2/items.md#yank Attempt 2] [round2/items.md#yank Attempt 3]; flat `/api/v1/proj/items/yank` is HTTP 404 `{"error":"not found"}` for DELETE and GET [round1/items.md#Attempt 20] [round1/items.md#Attempt 22].

### Identifiers and formats
- Project id: `proj_` + 6 lowercase hex chars, e.g. `proj_aa6cb4`; server-generated; case-sensitive on lookup. [round1/write.md#new Attempt 2] [round2/lifecycle.md#new Attempt 1] [round1/read.md#get-id Attempt 4]
- Todo id: `todo_` + 6 lowercase hex chars, e.g. `todo_fec6bd`; server-generated. [round1/items.md#Attempt 26] [round2/modify-touch.md#modify Attempt 10]
- Dates: `updated_at` (project) and the default `by` (todo) are Unix epoch milliseconds as JSON integers, e.g. `1793578023313`. `by` is stored as whatever the client sends, so a string or a negative number can appear in the same field. [round1/write.md#new Attempt 2] [round1/items.md#Attempt 27] [round2/items.md#add Attempt 1] [round2/items.md#add Attempt 2]
- `updated_at` semantics: set at creation; changed only by `POST .../touch`; frozen through modify, items/add, mark and yank. [round2/modify-touch.md#modify Attempt 2] [round2/modify-touch.md#touch Attempt 1] [round2/items.md#add Attempt 7] [round2/items.md#mark Attempt 9] [round2/items.md#yank Attempt 6]
- Status values: exactly `blocked`, `dropped`, `kickoff`, `wip`, `wrapped` (from the server's own validation message, identical on `/new` and `/modify`); all five appear in the seed data; default on create is `kickoff`. [round1/write.md#new Attempt 5] [round2/modify-touch.md#modify Attempt 4] [round1/read.md#list Attempt 1] [round1/read.md#list Attempt 2] [round1/write.md#new Attempt 2]
- Project shape: `description` (string, default `""`), `id`, `items` (array of todo, default `[]`), `status`, `title` (usually string; see Quirks), `updated_at`. [round1/write.md#new Attempt 2] [round2/lifecycle.md#new Attempt 1]
- Todo shape: `by`, `done` (boolean, always `false` at creation), `id`, `task`, `who` (default `""`). [round1/items.md#Attempt 26] [round2/items.md#add Attempt 4]
- Error body: always `{"error":"<message>"}`. Three 404 messages: `"not found"` = no route matched; `"no such project"` = a route matched but the project lookup failed; `"no such item"` = project found, todo not found in it. [round1/read.md#get-id Attempt 2] [round1/read.md#get-id Attempt 3] [round2/items.md#mark Attempt 5]
- Pagination: `from=0`, `take=5` by default; page size ceiling exactly 5. [round1/read.md#list Attempt 1] [round2/lifecycle.md#list Attempt 1] [round2/lifecycle.md#list Attempt 2]
- Seed data: 7 projects pre-exist (`proj_23315f`, `proj_756702`, `proj_ad713f`, `proj_338616`, `proj_e869bb`, `proj_828748`, `proj_bd0d1e`); do not modify or delete them. [round1/read.md#list Attempt 1] [round1/read.md#list Attempt 2]

## Quirks
- `updated_at` is frozen by every mutation except `touch`. Four successful modifies (title, status, description, `{}`), an items/add, a mark and a yank all left it at the creation value; only `POST .../touch` moved it. A client that wants "last modified" semantics must call touch itself after every write, and must not use `updated_at` to detect changes made by others. [round2/modify-touch.md#modify Attempt 2] [round2/modify-touch.md#modify Attempt 7] [round2/modify-touch.md#modify Attempt 11] [round2/items.md#add Attempt 7] [round2/items.md#mark Attempt 9] [round2/items.md#yank Attempt 6] [round2/modify-touch.md#touch Attempt 1]
- `touch` accepts a JSON body and ignores every field in it, so it cannot be used as "update and bump" in one call. [round2/modify-touch.md#touch Attempt 3]
- `modify` never rejects anything but a bad `status`: `{}` is a 200 no-op and `{"items":[]}` is a 200 that leaves the todos in place. Unknown or unsupported fields are dropped silently. [round2/modify-touch.md#modify Attempt 8] [round2/modify-touch.md#modify Attempt 12]
- OPTIONS works on a nested route once you know its path (`OPTIONS /api/v1/proj/{id}/remove` returns `Allow: DELETE, OPTIONS`), but the parent `OPTIONS /api/v1/proj/{id}` says only `GET, HEAD, OPTIONS`, so Allow headers cannot be used to enumerate children from a parent path. [round2/lifecycle.md#remove Attempt 8] [round1/remove.md#remove Attempt 7] [round1/items.md#Attempt 40]
- The flat paths from the brief (`/api/v1/proj/modify`, `/touch`, `/remove`, `/items`) are swallowed by the `GET /api/v1/proj/{project_id}` route with the literal word as the id: GET gives 404 `no such project`, every other verb gives 405, and OPTIONS advertises only `GET, HEAD, OPTIONS`. These 405s mean "wrong path", not "wrong verb". [round1/write.md#modify Attempt 3] [round1/write.md#modify Attempt 5] [round1/remove.md#remove Attempt 3] [round1/remove.md#remove Attempt 7] [round1/items.md#Attempt 2] [round1/items.md#Attempt 17]
- The real mutating routes nest ids as path segments (`/proj/{pid}/modify`, `/proj/{pid}/touch`, `/proj/{pid}/remove`, `/proj/{pid}/items/add`, `/proj/{pid}/items/{tid}/mark`), even though the id-less literal path for the sibling `/proj/new` is a real route. [round2/modify-touch.md#modify Attempt 1] [round2/modify-touch.md#touch Attempt 1] [round1/items.md#Attempt 25] [round1/items.md#Attempt 31] [round1/items.md#Attempt 40] [round1/remove.md#remove Attempt 9]
- No REST-style verbs on the resource itself: `DELETE`, `PUT` and `PATCH /api/v1/proj/{id}` are all 405. Deletion requires `/remove`, updates require `/modify`. [round1/remove.md#remove Attempt 12] [round2/lifecycle.md#get-id Attempt 2] [round2/lifecycle.md#get-id Attempt 3]
- Four distinct failure signals: 404 `not found` (no route), 405 `method not allowed` (route exists, verb rejected before body is read), 404 `no such project` (handler ran, project lookup failed), 404 `no such item` (project found, todo lookup failed). [round1/items.md#Attempt 13] [round1/items.md#Attempt 17] [round1/read.md#get-id Attempt 3] [round2/items.md#mark Attempt 5]
- Trailing slashes are never normalized; every path tried with one returned 404 `not found`, including working mutating routes with a valid body or id, and the target is left untouched (`/new/` creates nothing, `/{id}/remove/` deletes nothing). [round1/read.md#health Attempt 2] [round1/read.md#get-id Attempt 2] [round1/write.md#new Attempt 4] [round2/lifecycle.md#remove Attempt 6] [round2/lifecycle.md#remove Attempt 7] [round1/write.md#modify Attempt 13] [round1/write.md#touch Attempt 6]
- `remove` and `yank` are not idempotent: deleting twice returns 404, with the same body as deleting something that never existed. A client retrying a delete cannot distinguish "already gone" from "never there". [round2/lifecycle.md#remove Attempt 3] [round2/lifecycle.md#remove Attempt 4] [round2/items.md#yank Attempt 2]
- `mark` and `yank` are scoped to the project in the path; a real todo id under the wrong project is 404 `no such item`, indistinguishable from a bogus id. [round2/items.md#mark Attempt 6] [round2/items.md#yank Attempt 3]
- `take` above 5 is silently clamped and the response echoes the clamped value (`take=100` returns `"take":5`), so a client cannot detect the clamp from the echo alone. The ceiling is exactly 5 (`take=4` gives 4, `take=5` gives 5). [round1/read.md#list Attempt 8] [round1/read.md#list Attempt 11] [round2/lifecycle.md#list Attempt 1] [round2/lifecycle.md#list Attempt 2]
- `take=0` is accepted (empty page) and `from=-1` returns 200 with an empty page instead of 400, while `take=abc` is a 400. [round1/read.md#list Attempt 7] [round1/read.md#list Attempt 10] [round1/read.md#list Attempt 9]
- `id` and `status` query params on the list endpoint are silently ignored rather than rejected. [round1/read.md#list Attempt 5] [round1/read.md#list Attempt 6]
- `title` is checked for presence but not type: `""` is 400 `title is required`, yet `12345` is stored and returned as the JSON number `12345`, so project titles are not guaranteed to be strings. [round2/lifecycle.md#new Attempt 3] [round1/write.md#new Attempt 3] [round1/remove.md#list Attempt 4]
- `status` enum is case-sensitive lowercase on both create and modify, and the error message renders the set in Python list syntax (`['blocked', 'dropped', ...]`). [round1/write.md#new Attempt 8] [round2/modify-touch.md#modify Attempt 4]
- Todo field names are terse and non-obvious: `task` (not text/title), `who` (assignee), `by` (due), `flag` (for mark), and the delete verb is `yank`. [round1/items.md#Attempt 25] [round1/items.md#Attempt 26] [round1/items.md#Attempt 31] [round1/items.md#Attempt 36]
- `mark` wants `flag: "yes"|"no"` strings only. `"Yes"`, `true`, `"true"` and `1` are all 400, and the result lands in a field called `done`. [round1/items.md#Attempt 31] [round2/items.md#mark Attempt 1] [round2/items.md#mark Attempt 2] [round2/items.md#mark Attempt 3] [round2/items.md#mark Attempt 4]
- `by` (todo due) defaults to an epoch-ms value at request time rather than null, and accepts any JSON value verbatim (`"2026-12-01"`, `"not-a-date"`, `-1`). Readers must handle number and string. [round1/items.md#Attempt 26] [round1/items.md#Attempt 27] [round2/items.md#add Attempt 1] [round2/items.md#add Attempt 2]
- `who` defaults to `""`, not null or absent, and is not type-checked (`123` is stored as a number). [round1/items.md#Attempt 26] [round2/items.md#add Attempt 3]
- `done` cannot be set at todo creation; `{"task":"x","done":true}` creates a todo with `done:false` and no error. Use `mark` afterwards. [round2/items.md#add Attempt 4]
- Project ids are case-sensitive (`PROJ_23315F` is `no such project`). [round1/read.md#get-id Attempt 4]
- Sending a JSON body on GET produced an HTTP/2 stream error at the client (curl exit 92), not an API response. Do not send bodies on GET. [round1/write.md#modify Attempt 12]
- `total` in the list is live, not a snapshot: it moved 10 to 13 during one prober's session while others created fixtures, and drops immediately on remove. [round1/read.md#list Attempt 1] [round1/read.md#list Attempt 11] [round2/lifecycle.md#remove Attempt 16]

## Unresolved
- PUT /api/v1/proj/{id}/modify with JSON `{"id":"proj_23315f","title":"should-not-apply"}` on a fixture. Record whether the body `id` is ignored or overrides the path id (GET both ids afterwards; the seed project must be unchanged).
- POST /api/v1/proj/new with JSON `{"title":"r3-inline","items":[{"task":"t"}]}`. Record whether `items` is created inline or ignored (expect ignored, matching modify).
- POST /api/v1/proj/new with JSON `{"title":"r3-ids","id":"proj_custom","updated_at":1}`. Record whether the server-controlled `id` and `updated_at` are ignored or echoed.
- POST /api/v1/proj/does_not_exist/items/add with JSON `{"task":"x"}`. Record status and body (expect 404 `no such project`).
- POST /api/v1/proj/{id}/items/add with JSON `{"task":""}` and then `{"task":123}`. Record whether `task` gets the same presence-not-type check as `title` (400 for `""`, 201 for `123`).
