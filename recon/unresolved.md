# Unresolved after round 1

Route-shape reminder for round-two probers: ids go in the path (`/api/v1/proj/{project_id}/...`, `/api/v1/proj/{project_id}/items/{todo_id}/...`). The flat paths from the brief return 405/404 and prove nothing. Create your own fixtures with POST /api/v1/proj/new and delete them with DELETE /api/v1/proj/{id}/remove. Never touch the seven seed projects.

## PUT /api/v1/proj/modify (try as PUT /api/v1/proj/{project_id}/modify)
1. Create a fixture with POST /api/v1/proj/new `{"title":"r2-modify-1"}`, then PUT /api/v1/proj/{id}/modify with JSON `{"title":"r2-modify-1-renamed"}`. Record status, body, and whether GET /api/v1/proj/{id} shows the new title and a changed `updated_at`.
2. If that PUT is 405, send OPTIONS /api/v1/proj/{id}/modify and record the Allow header; then try POST and PATCH /api/v1/proj/{id}/modify with the same body and record which succeeds.
3. PUT /api/v1/proj/{id}/modify with `{"status":"wrapped"}`, then with `{"status":"WIP"}`. Record whether status changes and whether the same case-sensitive enum error from /new appears.
4. PUT /api/v1/proj/{id}/modify with `{"description":"r2 description"}`. Record whether `description` is updatable.
5. PUT /api/v1/proj/{id}/modify with `{}`. Record whether a 400 names required fields or a 200 returns the project unchanged.
6. PUT /api/v1/proj/{id}/modify with `{"id":"proj_23315f","title":"should-not-apply"}`. Record whether a body `id` is ignored or overrides the path id (check GET on both ids afterwards).
7. PUT /api/v1/proj/does_not_exist/modify with `{"title":"x"}`. Record status and body.
8. PUT /api/v1/proj/{id}/modify with `{"items":[]}` on a project that has one todo. Record whether items can be wiped through modify.

## POST /api/v1/proj/touch (try as POST /api/v1/proj/{project_id}/touch)
1. GET /api/v1/proj/{id} and note `updated_at`; wait at least 1 second; POST /api/v1/proj/{id}/touch with no body. Record status, body, and whether `updated_at` increased on a following GET.
2. If that POST is 405, send OPTIONS /api/v1/proj/{id}/touch and record the Allow header; then try PUT and PATCH on the same path.
3. POST /api/v1/proj/{id}/touch with JSON `{"status":"wip","title":"touched"}`. Record whether touch applies any fields or ignores the body.
4. POST /api/v1/proj/does_not_exist/touch. Record status and body.

## DELETE /api/v1/proj/remove (real route: DELETE /api/v1/proj/{project_id}/remove)
1. Create a fixture, DELETE /api/v1/proj/{id}/remove and record the 200 body; then DELETE the same path again. Record status and body of the second call.
2. DELETE /api/v1/proj/does_not_exist/remove. Record status and body.
3. DELETE /api/v1/proj/{id}/remove/ (trailing slash) on a live fixture. Record status and whether the fixture survived.
4. OPTIONS /api/v1/proj/{id}/remove and record the Allow header; then POST /api/v1/proj/{id}/remove and record whether POST also deletes.
5. After a successful remove, GET /api/v1/proj/{id} and GET /api/v1/proj?from=0. Record that the first is 404 `no such project` and `total` dropped by one.

## POST /api/v1/proj/new
1. POST /api/v1/proj/new with `{"title":"r2-desc","description":"hello"}`. Record whether `description` is stored.
2. POST /api/v1/proj/new with `{"title":""}`. Record 400 vs 201.
3. POST /api/v1/proj/new with `{"title":"r2-inline","items":[{"task":"t"}]}`. Record whether items can be created inline or are ignored.
4. POST /api/v1/proj/new with `{"title":"r2-ids","id":"proj_custom","updated_at":1}`. Record whether server-controlled fields are ignored or echoed.
5. POST /api/v1/proj/new with `Content-Type: application/x-www-form-urlencoded` body `title=r2-form`. Record whether form bodies are accepted.

## GET /api/v1/proj
1. GET /api/v1/proj?take=5 and GET /api/v1/proj?take=4. Record the project count and echoed `take` to pin the ceiling at exactly 5.
2. GET /api/v1/proj?from=-5 and GET /api/v1/proj?from=999. Record status, echoed `from`, and project count.
3. GET /api/v1/proj?from=1.5 and GET /api/v1/proj?take=-1. Record status and message.
4. GET /api/v1/proj?from=0&take=5 then ?from=5&take=5 then ?from=10&take=5 and record whether order is stable creation order (compare `updated_at` sequence across pages).

## GET /api/v1/proj/{project_id}
1. GET /api/v1/proj/proj_23315f?take=1&status=wip. Record whether query params are ignored on the single-project route.
2. PUT /api/v1/proj/{id} and PATCH /api/v1/proj/{id} with `{"title":"x"}`. Record 405 vs anything else.

## GET /api/v1/proj/items (real route: GET /api/v1/proj/{project_id}/items)
1. GET /api/v1/proj/does_not_exist/items. Record status and body.
2. GET /api/v1/proj/{id}/items/ (trailing slash). Record status and body.
3. GET /api/v1/proj/{id}/items?from=0&take=1 on a project with 2 or more todos. Record whether the items list paginates.

## POST /api/v1/proj/items/add (real route: POST /api/v1/proj/{project_id}/items/add)
1. POST /api/v1/proj/does_not_exist/items/add with `{"task":"x"}`. Record status and body.
2. POST /api/v1/proj/{id}/items/add with `{"task":"x","by":"not-a-date"}`, then `{"task":"x","by":-1}`, then `{"task":"x","who":123}`. Record which, if any, are rejected.
3. POST /api/v1/proj/{id}/items/add with `{"task":"x","done":true}`. Record whether `done` can be set at creation.
4. POST /api/v1/proj/{id}/items/add with `{"task":""}` and `{"task":123}`. Record status and body.
5. GET /api/v1/proj/{id}, add a todo, GET /api/v1/proj/{id} again. Record whether the project's `updated_at` changed and whether the project's `items` array includes the new todo.

## POST /api/v1/proj/items/mark (real route: POST /api/v1/proj/{project_id}/items/{todo_id}/mark)
1. POST /api/v1/proj/{id}/items/{tid}/mark with `{"flag":"Yes"}`, `{"flag":true}`, `{"flag":"true"}`, `{"flag":1}`. Record which are 400 and the exact message.
2. POST /api/v1/proj/{id}/items/todo_bogus/mark with `{"flag":"yes"}`. Record status and body.
3. POST /api/v1/proj/{other_id}/items/{tid}/mark with `{"flag":"yes"}` where `tid` belongs to a different project. Record whether the project scope is enforced.
4. Mark a todo and GET /api/v1/proj/{id} before and after. Record whether the project's `updated_at` changes.

## DELETE /api/v1/proj/items/yank (real route: DELETE /api/v1/proj/{project_id}/items/{todo_id}/yank)
1. DELETE /api/v1/proj/{id}/items/{tid}/yank twice. Record status and body of the second call.
2. DELETE /api/v1/proj/{id}/items/todo_bogus/yank. Record status and body.
3. DELETE /api/v1/proj/{other_id}/items/{tid}/yank where `tid` belongs to a different project. Record whether it is refused.
4. Yank a todo and GET /api/v1/proj/{id} before and after. Record whether the project's `updated_at` changes.
