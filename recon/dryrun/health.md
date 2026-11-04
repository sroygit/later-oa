# Findings: dryrun (round 0)

Base URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Calls used: 3 of 40

## GET /api/v1/health

### Attempt 1
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/health
Headers: none
Body: none
Response: HTTP 200
```
{"status":"ok"}
```

### Attempt 2
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/health/
Headers: none
Body: none
Response: HTTP 404
```
{"error":"not found"}
```
Note: trailing slash is not accepted; path is matched exactly.

### Attempt 3
Request: GET https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app/api/v1/health?id=1
Headers: none
Body: none
Response: HTTP 200
```
{"status":"ok"}
```
Note: extraneous query params are silently ignored.

## Could not determine
- Whether any other HTTP methods (POST, PUT, DELETE) are accepted on /api/v1/health, since the dry-run scope restricted this to GET only.

## Cleanup
- No fixture calls were made in this dry run; no projects were created, so no cleanup was required.
