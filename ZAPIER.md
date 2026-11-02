# Andy: marking todos complete from Zapier / Make / n8n / Gumloop

The raw API wants ids in the URL path and a literal `"yes"` flag. No-code tools are bad at that.
So run the shim and point your tool at it with plain names.

## 1. Run the shim and expose it

(The same process also serves Betty's page at <http://localhost:8787> and Dan's MCP server at `/mcp`; Andy's routes below are unaffected.)

```
.venv/bin/uvicorn webhook:app --port 8787
ngrok http 8787        # copy the https URL it prints
```

## 2. Zapier: "Webhooks by Zapier" action

| Field | Value |
|---|---|
| Event | POST |
| URL | `https://<your-ngrok>.ngrok.app/complete` |
| Payload Type | Form |
| Data | `project` = the project title (or a unique fragment, e.g. `spring`) <br> `todo` = the todo text (or a fragment, e.g. `sign-off`) |

That's it. Map `project` and `todo` from the trigger step (Slack message text, form field, calendar title).

Optional: add `done` = `no` to un-complete instead.

### Add a todo instead

Same action, URL `/add`, fields `project`, `task`, optional `who`, optional `due`.

`due` can be the raw text from the trigger — you do not have to format it. ISO (`2026-11-07`),
epoch ms, or plain English: `next Friday`, `tomorrow`, `in 3 days`, `end of month`, `Nov 7`.
Weekday names mean the *next* one, so a Zap that fires on a Friday and maps `due` = `Friday`
gets the following Friday, not today. Map the whole Slack message fragment straight in.
If the text isn't a date at all, the shim answers `400 could not parse due date: '<text>'`,
so the Zap fails loudly instead of silently writing a wrong due date. Leave `due` empty for
no due date.

### Trigger on overdue todos

Schedule by Zapier (daily) → Webhooks GET `https://<ngrok>/late` → loop over the array.

## Make / n8n / Gumloop

Same two endpoints. HTTP Request node, POST, body type form or JSON, same field names.
GET works too: `/complete?project=spring&todo=sign-off`, so even a bare URL action is enough.

## Why not hit the API directly

You can. The exact call is
`POST https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/proj/{project_id}/items/{todo_id}/mark`
with JSON `{"flag": "yes"}`. But then every Zap needs two lookups first (title→project id, text→todo id),
and the list endpoint only returns 5 projects per page. The shim does that resolution for you.
