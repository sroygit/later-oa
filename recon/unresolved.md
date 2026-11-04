# Unresolved after round 2

Deprioritised, not listed: pagination edge cases (`from=-5`, `from=999`, `from=1.5`, `take=-1`, cross-page ordering, items-list pagination) and form-encoded bodies, because the client walks pages with `from`/`take<=5` and only sends JSON. Trailing slash on nested routes is covered by the confirmed rule that no trailing slash is ever accepted.

Route-shape reminder: ids go in the path (`/api/v1/proj/{project_id}/...`, `/api/v1/proj/{project_id}/items/{todo_id}/...`). Create fixtures with POST /api/v1/proj/new and delete them with DELETE /api/v1/proj/{id}/remove. Never touch the seven seed projects.

## PUT /api/v1/proj/{project_id}/modify
1. PUT /api/v1/proj/{id}/modify with JSON `{"id":"proj_23315f","title":"should-not-apply"}` on a fixture. Record whether the body `id` is ignored or overrides the path id (GET both ids afterwards; the seed project must be unchanged).

## POST /api/v1/proj/new
1. POST /api/v1/proj/new with JSON `{"title":"r3-inline","items":[{"task":"t"}]}`. Record whether `items` is created inline or ignored (expect ignored, matching modify).
2. POST /api/v1/proj/new with JSON `{"title":"r3-ids","id":"proj_custom","updated_at":1}`. Record whether the server-controlled `id` and `updated_at` are ignored or echoed.

## POST /api/v1/proj/{project_id}/items/add
1. POST /api/v1/proj/does_not_exist/items/add with JSON `{"task":"x"}`. Record status and body (expect 404 `no such project`).
2. POST /api/v1/proj/{id}/items/add with JSON `{"task":""}` and then `{"task":123}`. Record whether `task` gets the same presence-not-type check as `title` (400 for `""`, 201 for `123`).
