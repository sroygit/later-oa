# Self-Improving Recon Agents — Design

Date: 2026-11-01
Status: approved in conversation, awaiting written review
Context: Later AI Automation Engineer take-home (see `HANDOFF.md`). 1.5 hour hard cap, graded on choices.

## Purpose

Reverse-engineer the undocumented Projects API using a two-tier agent system: cheap Sonnet probers do wide mechanical probing, Fable agents synthesize the findings and rewrite the probers' prompt between rounds. The system is part of the demo story, so every agent run and every prompt rewrite is logged to files.

The client wrapper and the four persona surfaces are built directly by the human and the orchestrating Claude session, not by agents.

## Decisions already made

| Question | Decision |
|---|---|
| What "self-improving" means | The Fable reviewer rewrites `.claude/agents/prober.md` between rounds and logs the rationale. |
| Clock | Agent definitions are written pre-clock with no API calls. The clock starts at the first round-one dispatch. |
| Scope | Agents do recon and review only. Client and persona surfaces are built directly. |
| Demo | The system is shown to interviewers. It lives in the OA folder with a run log and a changelog. |
| Orchestration | Approach B: the orchestrating Claude session dispatches agents with the Agent tool and reads every output between tiers. No workflow script, no standalone orchestrator. |
| Rounds | Exactly two. Round one is broad, round two is narrow and driven by the unresolved list. |

## Layout

```
.claude/agents/prober.md        Sonnet. Probes an endpoint slice, writes raw findings.
.claude/agents/synthesizer.md   Fable. Reads all findings, writes API_NOTES.md.
.claude/agents/reviewer.md      Fable. Grades the probers' work, rewrites prober.md.
recon/round1/<slice>.md         Raw prober output, round one.
recon/round2/<slice>.md         Raw prober output, round two.
recon/unresolved.md             Synthesizer's open questions, drives round two.
recon/RUNLOG.md                 One entry per agent run: who, what, when, outcome.
recon/PROMPT_CHANGELOG.md             Reviewer's prompt rewrites with rationale.
API_NOTES.md                    The deliverable: the docs Later never gave.
```

## Agents

### Prober (Sonnet)

Input: one endpoint slice, the base URL, the probe protocol embedded in its prompt, and the path of its output file.

Protocol, for each endpoint in the slice:
1. Try the method with query params, then JSON body, then form body, with plausible field names.
2. Record the exact request (method, URL, headers that matter, body) and the exact response (status, body verbatim). Never summarize, never guess.
3. Vary one thing at a time: missing fields, wrong types, unknown ids, trailing slash on and off, uppercase vs lowercase values.
4. Only create, modify, or delete projects whose title starts with the slice name. Never touch any other project.
5. Delete everything it created at the end, and record whether the delete succeeded.

Output: one markdown file with a section per endpoint and a final "things I could not determine" list. Appends one line to `recon/RUNLOG.md`.

### Synthesizer (Fable)

Input: every file under `recon/round1/` (and `recon/round2/` on the final pass).

Output: `API_NOTES.md` with three sections: confirmed behaviour per endpoint (request shape, response shape, id format, date format, status codes), quirks, and unresolved questions. The unresolved questions are also written to `recon/unresolved.md` as concrete probe instructions, each tagged with the endpoint it concerns. Appends to the run log.

### Reviewer (Fable)

Input: the round-one findings, `recon/unresolved.md`, and the current `.claude/agents/prober.md`.

Task: identify what the probers did badly. Expected failure classes: missed a payload shape, guessed instead of testing, recorded prose instead of raw output, exceeded its slice, left test data behind. Rewrite `prober.md` to fix those failures. Append an entry to `recon/PROMPT_CHANGELOG.md` with the before and after of each changed instruction and one sentence of rationale per change. Appends to the run log.

The reviewer does not touch the synthesizer's or its own prompt. One loop edge, kept narrow.

## Round-one slices

| Slice | Endpoints |
|---|---|
| `read` | GET /api/v1/health, GET /api/v1/proj, GET /api/v1/proj/ |
| `write` | POST /api/v1/proj/new, PUT /api/v1/proj/modify, POST /api/v1/proj/touch |
| `remove` | DELETE /api/v1/proj/remove (alone, because it is destructive) |
| `items` | GET /api/v1/proj/items, POST /api/v1/proj/items/add, POST /api/v1/proj/items/mark, DELETE /api/v1/proj/items/yank |

Round-two slices are derived from `recon/unresolved.md`, grouped by endpoint, usually two or three probers.

## Run sequence

Pre-clock:
1. Write the three agent definitions.
2. Dispatch one prober with a dry-run slice containing only the health endpoint, to verify the Agent tool loads definitions from the project folder. Health was already confirmed live, so this reveals nothing about the API.

On-clock, starting at step 3:
3. Round one: four probers in parallel. Wait for all. About 5 minutes.
4. Synthesize: one Fable run over round one. Orchestrator reads the notes and the unresolved list. About 3 minutes.
5. Review and rewrite: one Fable run. Orchestrator reads the diff to `prober.md` and reverts if wrong, logging the revert. About 2 minutes.
6. Round two: probers over the unresolved list with the rewritten prompt. About 4 minutes.
7. Finalize: synthesizer reruns over both rounds and produces the final notes. About 2 minutes.
8. Hand off. Client and persona surfaces built directly, following `HANDOFF.md` from the 15 minute mark.

## Failure handling

- A prober hangs or errors: proceed with the rest, note the gap in the unresolved list, round two covers it.
- Probers collide on shared state: prevented by the title-prefix rule. A prober seeing a project it did not create records it as a finding (evidence the list endpoint has no filtering), not a bug.
- API restarts mid-run: findings are keyed on request and response, not ids, so they stay valid. Round two recreates what it needs.
- Round two leaves questions: stop anyway. Unresolved items go into the notes as known unknowns and into the decisions file.

## Orchestrator responsibilities

The orchestrating session reads every agent output before dispatching the next tier. When it corrects an agent's output by hand, it records the correction in `recon/RUNLOG.md`, so the demo shows where the human overrode the agents.

## Out of scope

- A third round or an open-ended loop.
- The reviewer editing any prompt other than the prober's.
- Agents building the client or persona surfaces.
- A workflow script or standalone orchestrator.
