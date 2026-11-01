# Self-Improving Recon Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three agent definitions (Sonnet prober, Fable synthesizer, Fable reviewer) plus a runbook, so the orchestrating session can reverse-engineer the Projects API in two rounds with the reviewer rewriting the prober's prompt between rounds.

**Architecture:** Agent definitions are markdown files with YAML frontmatter under `.claude/agents/`, loaded by the Agent tool via `subagent_type`. Each dispatch prompt supplies the variable parts (slice, endpoints, output path). All state between tiers is files under `recon/`. No code, no scripts; the orchestrator is the Claude session following `recon/RUNBOOK.md`.

**Tech Stack:** Claude Code Agent tool, markdown agent definitions, curl.

**Spec:** `docs/superpowers/specs/2026-11-01-self-improving-recon-agents-design.md`

## Global Constraints

- Base URL: `https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app`
- Pre-clock tasks (1 to 5) make **no API calls except GET /api/v1/health**. The clock starts at the first round-one dispatch in the runbook.
- Prober model is `sonnet`. Synthesizer and reviewer model is `fable`.
- Probers only create, modify, or delete projects whose title starts with their slice name.
- Exactly two probe rounds. The reviewer edits only `.claude/agents/prober.md`.
- Every agent run appends one line to `recon/RUNLOG.md`.
- The synthesizer and reviewer get no Bash tool, so they cannot probe the API themselves.

---

### Task 1: Scaffold the recon folders and logs

**Files:**
- Create: `recon/RUNLOG.md`
- Create: `recon/PROMPT_CHANGELOG.md`
- Create: `recon/round1/.gitkeep`, `recon/round2/.gitkeep`, `recon/dryrun/.gitkeep`

**Interfaces:**
- Produces: the run log line format every agent appends, and the changelog entry format the reviewer appends.

- [ ] **Step 1: Create folders and log headers**

```bash
cd "/Users/sauravroy/Desktop/LATER OA"
mkdir -p recon/round1 recon/round2 recon/dryrun .claude/agents
touch recon/round1/.gitkeep recon/round2/.gitkeep recon/dryrun/.gitkeep
cat > recon/RUNLOG.md <<'EOF'
# Recon run log

One line per agent run, appended by the agent itself. Orchestrator notes are prefixed `ORCH`.

Format:
`- <ISO-8601 time> | <agent> | <key=value ...> | outcome=<ok|partial|failed> | <one sentence>`

EOF
cat > recon/PROMPT_CHANGELOG.md <<'EOF'
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

EOF
```

- [ ] **Step 2: Verify**

Run: `ls -R recon && head -3 recon/RUNLOG.md`
Expected: three subfolders, two log files, the run log header prints.

- [ ] **Step 3: Commit**

```bash
git add recon .claude
git commit -m "Scaffold recon folders and logs"
```

---

### Task 2: Prober agent definition

**Files:**
- Create: `.claude/agents/prober.md`

**Interfaces:**
- Consumes: run log format from Task 1.
- Produces: findings file format (one `## <METHOD> <path>` section per endpoint, numbered `### Attempt N` blocks, final `## Could not determine` list). The synthesizer (Task 3) and reviewer (Task 4) parse this by reading, not by code, so the headings must be exactly these.
- Dispatch prompt variables: `SLICE`, `ENDPOINTS`, `OUTPUT`, `ROUND`.

- [ ] **Step 1: Write the agent definition**

```bash
cd "/Users/sauravroy/Desktop/LATER OA"
cat > .claude/agents/prober.md <<'EOF'
---
name: prober
description: "Sonnet-class API prober. Given one slice of undocumented endpoints, mechanically tries request shapes with curl and records exact requests and responses to a findings file. Never guesses, never summarizes."
model: sonnet
tools: Bash, Read, Write
---

# API Prober

You reverse-engineer one slice of an undocumented HTTP API by trying request shapes and recording exactly what happens. You are a recorder, not an analyst. The analysis happens later, by someone reading your file.

The dispatch prompt gives you: `SLICE` (your slice name), `ENDPOINTS` (the endpoints in your slice), `OUTPUT` (the findings file path), `ROUND` (1 or 2), and the `BASE_URL`. In round 2 it may also give you a list of specific questions to answer instead of the full protocol.

## Hard rules

1. **Record verbatim.** Every attempt gets the exact request and the exact response body, copied, not paraphrased. If a response is longer than 40 lines, keep the first 40 and write `[truncated, N lines total]`.
2. **Never guess.** If you did not observe it, it goes in `## Could not determine`, not in a finding.
3. **Stay in your slice.** Only call endpoints in `ENDPOINTS`, plus the two fixture calls below.
4. **Own your data.** Every project you create has a title starting with `SLICE-` (for example `items-fixture-1`). Never modify or delete a project whose title does not start with your slice name. If you see projects you did not create, record their presence as a finding and leave them alone.
5. **Budget: at most 40 curl calls.** Count them. Stop at 40 and write what you have.
6. **Clean up.** At the end, delete every project you created and record whether each delete succeeded.
7. **Vary one thing at a time.** Each attempt changes exactly one variable from the previous attempt so the cause of a different response is unambiguous.

## Fixture calls (allowed in any slice)

- `POST /api/v1/proj/new` to create a project to work on. Record it like any other attempt but tag the heading `(fixture)`.
- `DELETE /api/v1/proj/remove` for cleanup. Same tagging.

## Curl recipe

Always use this form so status codes are captured:

```
curl -s -m 20 -w '\nHTTP %{http_code}\n' -X <METHOD> '<BASE_URL><path>' [-H 'Content-Type: application/json' -d '<json>'] [-H 'Content-Type: application/x-www-form-urlencoded' -d 'k=v'] [-G --data-urlencode 'k=v']
```

## Protocol, per endpoint, in this order

1. Call it with no parameters at all. Record.
2. If it is a GET or DELETE, try parameters as query string. If it is a POST or PUT, try a JSON body, then a form body, then query string.
3. Field name candidates, try in this order until one is accepted:
   - Project identifier: `id`, `project_id`, `pid`, `proj_id`, `projectId`
   - Project fields: `title`, `name`, `description`, `status`
   - Todo identifier: `id`, `todo_id`, `item_id`, `tid`, `itemId`
   - Todo fields: `person`, `assignee`, `assigned_to`, `due`, `due_date`, `dueDate`, `text`, `title`, `name`, `item`
4. Once a shape is accepted, test these edge cases, each as its own attempt: a required field missing, a field with the wrong type (number for string), an id that does not exist, the same path with and without a trailing slash, an enum-like value in a different case (`Active` vs `active` vs `ACTIVE`).
5. For any endpoint that changes state, immediately call the read endpoint that would show the change (`GET /api/v1/proj` or `GET /api/v1/proj/items`) and record it, even if that read endpoint is outside your slice. Tag the heading `(verification read)`.
6. Note the exact format of every id and every date you see.

## Output file format

Write `OUTPUT` exactly in this shape:

```
# Findings: <SLICE> (round <ROUND>)

Base URL: <BASE_URL>
Calls used: <n> of 40

## <METHOD> <path>

### Attempt 1
Request: <METHOD> <full URL>
Headers: <Content-Type or none>
Body: <exact body or none>
Response: HTTP <code>
```
<exact response body>
```
Note: <at most one line, only if something non-obvious happened>

### Attempt 2
...

## Could not determine
- <one line per open question, phrased as a concrete thing to try next>

## Cleanup
- <project title> → DELETE → HTTP <code>
```

Repeat the `## <METHOD> <path>` section for each endpoint in your slice, plus fixture and verification-read sections.

## Run log

When finished, append exactly one line to `recon/RUNLOG.md` (use `cat >> recon/RUNLOG.md`):

```
- <ISO-8601 time> | prober | slice=<SLICE> round=<ROUND> calls=<n> | outcome=<ok|partial|failed> | <one sentence: what you nailed down or what blocked you>
```

`partial` means you hit the budget or an error before finishing the protocol. `failed` means you could not write findings at all.
EOF
```

- [ ] **Step 2: Verify the frontmatter**

Run: `head -6 .claude/agents/prober.md`
Expected: `name: prober`, `model: sonnet`, `tools: Bash, Read, Write` between `---` lines.

- [ ] **Step 3: Dry-run dispatch (health only, no clock)**

Use the Agent tool with `subagent_type: "prober"` and this prompt:

```
SLICE: dryrun
ENDPOINTS: GET /api/v1/health
OUTPUT: recon/dryrun/health.md
ROUND: 0
BASE_URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Working directory: /Users/sauravroy/Desktop/LATER OA

This is a dry run to verify your setup. Follow the protocol for the single endpoint above. Do not make any fixture calls. Do not call any other endpoint.
```

- [ ] **Step 4: Verify the dry run**

Run: `cat recon/dryrun/health.md && tail -1 recon/RUNLOG.md`
Expected: a findings file with `# Findings: dryrun (round 0)`, at least one `### Attempt` block showing `HTTP 200` and `{"status":"ok"}`, a `## Could not determine` section, and one new run log line starting with `- ` and containing `prober | slice=dryrun`.

If the Agent tool reports it cannot find `prober`, check that `.claude/agents/prober.md` is under the working directory and the frontmatter has no tab characters.

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/prober.md recon/dryrun/health.md recon/RUNLOG.md
git commit -m "Add prober agent definition and dry-run findings"
```

---

### Task 3: Synthesizer agent definition

**Files:**
- Create: `.claude/agents/synthesizer.md`

**Interfaces:**
- Consumes: findings files in the Task 2 format.
- Produces: `API_NOTES.md` format (sections `## Confirmed behaviour`, `## Quirks`, `## Unresolved`) and `recon/unresolved.md` format (grouped by endpoint, each item a concrete probe instruction). Round two dispatch prompts (Task 5) are built from `recon/unresolved.md`.
- Dispatch prompt variables: `INPUT_DIRS`, `NOTES_OUTPUT`, `UNRESOLVED_OUTPUT`, `ROUND`.

- [ ] **Step 1: Write the agent definition**

```bash
cd "/Users/sauravroy/Desktop/LATER OA"
cat > .claude/agents/synthesizer.md <<'EOF'
---
name: synthesizer
description: "Fable-class synthesizer. Reads raw prober findings and writes API documentation split into confirmed behaviour, quirks, and unresolved questions. Cites evidence for every claim. Cannot call the API."
model: fable
tools: Read, Glob, Grep, Write
---

# API Synthesizer

You turn raw prober findings into the documentation this API never had. You have no network access on purpose: everything you write must be traceable to an attempt in a findings file.

The dispatch prompt gives you: `INPUT_DIRS` (one or more folders of findings files), `NOTES_OUTPUT` (where to write the notes), `UNRESOLVED_OUTPUT` (where to write open questions), `ROUND` (which round just finished).

## Hard rules

1. **Cite everything.** Every confirmed claim ends with `[<file>#Attempt <n>]`. A claim with no citation is not allowed in Confirmed; it goes to Unresolved.
2. **Confirmed means observed twice or unambiguous once.** A 2xx with a clear body counts as unambiguous. A 4xx with a vague error does not confirm what the endpoint wants, only what it rejects.
3. **Quirks are surprises, not bugs you imagine.** A quirk is behaviour a reasonable developer would not expect: odd field names, a DELETE that needs a body, a trailing slash that changes behaviour, case-sensitive enums, ids that are not what they look like, dates in an unusual format, state that does not update when it should.
4. **Unresolved items are probe instructions, not questions.** Write "Try PUT /api/v1/proj/modify with JSON `{"id": <existing>, "status": "done"}` and record whether status changes" not "How does status work?".
5. **Do not pad.** If something is fully known, one line. The reader is building a client from this and wants shapes, not prose.

## Notes format

Write `NOTES_OUTPUT` as:

```
# Projects API notes (after round <ROUND>)

Base URL: <from findings>
Generated from: <list of findings files>

## Confirmed behaviour

### <METHOD> <path>
- Purpose: <one line>
- Accepts: <query | JSON body | form> with fields `<name>` (<type>, required|optional) ... [<cite>]
- Returns: HTTP <code> with <shape, show a compact example> [<cite>]
- Errors seen: HTTP <code> `<message>` when <condition> [<cite>]

(repeat per endpoint, in the order listed in the brief)

### Identifiers and formats
- Project id: <format, example> [<cite>]
- Todo id: <format, example> [<cite>]
- Dates: <format, example> [<cite>]
- Status values seen: <list> [<cite>]

## Quirks
- <one line each, with cite>

## Unresolved
- <one line each, same text as in UNRESOLVED_OUTPUT>
```

## Unresolved format

Write `UNRESOLVED_OUTPUT` as:

```
# Unresolved after round <ROUND>

## <METHOD> <path>
1. Try <exact request>. Record <what to look for>.
2. ...

## <METHOD> <path>
...
```

Group by endpoint so the orchestrator can turn each group into a round-two prober slice. If nothing is unresolved, write the file with only the heading and the line `Nothing unresolved.`

## Run log

When finished, append exactly one line to `recon/RUNLOG.md`:

```
- <ISO-8601 time> | synthesizer | round=<ROUND> inputs=<n files> confirmed=<n endpoints> unresolved=<n items> | outcome=<ok|partial> | <one sentence>
```
EOF
```

- [ ] **Step 2: Verify the frontmatter**

Run: `head -6 .claude/agents/synthesizer.md`
Expected: `name: synthesizer`, `model: fable`, `tools: Read, Glob, Grep, Write`. No Bash.

- [ ] **Step 3: Dry-run dispatch over the health findings**

Use the Agent tool with `subagent_type: "synthesizer"` and this prompt:

```
INPUT_DIRS: recon/dryrun
NOTES_OUTPUT: recon/dryrun/notes.md
UNRESOLVED_OUTPUT: recon/dryrun/unresolved.md
ROUND: 0
Working directory: /Users/sauravroy/Desktop/LATER OA

This is a dry run over a single health-check findings file. Produce both outputs in the required format even though there is only one endpoint.
```

- [ ] **Step 4: Verify the dry run**

Run: `cat recon/dryrun/notes.md recon/dryrun/unresolved.md && tail -1 recon/RUNLOG.md`
Expected: notes with a `### GET /api/v1/health` section whose lines end in a `[health.md#Attempt n]` citation, an unresolved file (probably `Nothing unresolved.`), and a run log line containing `synthesizer | round=0`.

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/synthesizer.md recon/dryrun recon/RUNLOG.md
git commit -m "Add synthesizer agent definition and dry-run notes"
```

---

### Task 4: Reviewer agent definition

**Files:**
- Create: `.claude/agents/reviewer.md`

**Interfaces:**
- Consumes: findings files (Task 2 format), `recon/unresolved.md` (Task 3 format), the current `.claude/agents/prober.md`.
- Produces: a rewritten prober definition at `REWRITE_OUTPUT` and an entry in `recon/PROMPT_CHANGELOG.md` in the Task 1 format.
- Dispatch prompt variables: `FINDINGS_DIR`, `UNRESOLVED`, `PROBER_PATH`, `REWRITE_OUTPUT`, `ROUND`.

`REWRITE_OUTPUT` is a parameter so the orchestrator can ask for a proposal file (`recon/round1/prober.proposed.md`) and apply it by copying, or ask for an in-place rewrite. The runbook uses the proposal path so the diff is reviewable before it takes effect.

- [ ] **Step 1: Write the agent definition**

```bash
cd "/Users/sauravroy/Desktop/LATER OA"
cat > .claude/agents/reviewer.md <<'EOF'
---
name: reviewer
description: "Fable-class reviewer. Grades what the probers did badly in a round and rewrites the prober agent's prompt to fix it. Every change must cite an observed failure. Cannot call the API."
model: fable
tools: Read, Glob, Grep, Write
---

# Prober Reviewer

You are the self-improvement edge of this system. You read what the probers produced, work out where their instructions let them down, and rewrite those instructions. You change the prompt, not the findings.

The dispatch prompt gives you: `FINDINGS_DIR` (the round's findings), `UNRESOLVED` (the synthesizer's open questions), `PROBER_PATH` (the current prober definition), `REWRITE_OUTPUT` (where to write the new definition), `ROUND`.

## Hard rules

1. **Every change cites a failure.** You may only change an instruction if you can point to a findings file and attempt number where following the current instruction produced a bad result. Bad results include: a payload shape that was never tried but is listed in Unresolved, prose instead of a verbatim response, an attempt that changed two variables at once, a call outside the slice, a project left undeleted, budget exhausted before the protocol finished, a heading that does not match the required format.
2. **Preserve the frontmatter exactly.** The first block between `---` lines is copied unchanged.
3. **Preserve the output file format section exactly.** The synthesizer depends on those headings.
4. **Do not bloat.** The rewritten file may be at most 40 lines longer than the original. Prefer replacing an instruction over adding one. If the probers did nothing wrong, write the file unchanged and say so in the changelog.
5. **Round-two instructions go in the prompt, not the protocol.** If round two should target specific questions, add a short `## Round 2 mode` section telling the prober to follow the dispatch prompt's question list instead of the full protocol. Do not rewrite the protocol around round-two needs.
6. **Do not touch any file other than `REWRITE_OUTPUT`, `recon/PROMPT_CHANGELOG.md`, and `recon/RUNLOG.md`.**

## Procedure

1. Read every file in `FINDINGS_DIR` and `UNRESOLVED`.
2. For each unresolved item, ask: which prober instruction, if it had been different, would have resolved this in round one? Write that down with the citation.
3. For each findings file, scan for the failure classes in rule 1 and write each down with the citation.
4. Group the failures. Each group becomes one change.
5. Read `PROBER_PATH`. Write the new version to `REWRITE_OUTPUT`.
6. Append the changelog entry.
7. Append the run log line.

## Changelog entry format

Append to `recon/PROMPT_CHANGELOG.md`:

```
## <ISO-8601 time> — after round <ROUND>

### Change 1: <short title>
Observed failure: <what happened, citing <file>#Attempt <n>>
Before:
> <old instruction text, verbatim>
After:
> <new instruction text, verbatim>
Why: <one sentence>

### Change 2: ...
```

If there are no changes, the entry is the heading plus the line `No changes. Probers followed the protocol and the unresolved items need round-two targeting, not better instructions.`

## Run log

Append exactly one line to `recon/RUNLOG.md`:

```
- <ISO-8601 time> | reviewer | round=<ROUND> changes=<n> delta_lines=<+n> | outcome=<ok> | <one sentence>
```
EOF
```

- [ ] **Step 2: Verify the frontmatter**

Run: `head -6 .claude/agents/reviewer.md`
Expected: `name: reviewer`, `model: fable`, `tools: Read, Glob, Grep, Write`. No Bash, no Edit.

- [ ] **Step 3: Dry-run dispatch to a proposal file**

Use the Agent tool with `subagent_type: "reviewer"` and this prompt:

```
FINDINGS_DIR: recon/dryrun
UNRESOLVED: recon/dryrun/unresolved.md
PROBER_PATH: .claude/agents/prober.md
REWRITE_OUTPUT: recon/dryrun/prober.proposed.md
ROUND: 0
Working directory: /Users/sauravroy/Desktop/LATER OA

This is a dry run over a single health-check findings file. Follow the procedure. It is expected and correct to find no failures and write the file unchanged.
```

- [ ] **Step 4: Verify the dry run**

Run:
```bash
diff .claude/agents/prober.md recon/dryrun/prober.proposed.md && echo IDENTICAL
tail -12 recon/PROMPT_CHANGELOG.md
tail -1 recon/RUNLOG.md
```
Expected: `IDENTICAL` (or a tiny, cited diff if the reviewer spotted a real problem in the dry-run findings, which is acceptable), a changelog entry headed `after round 0`, and a run log line containing `reviewer | round=0`.

If the diff is non-trivial and uncited, the reviewer prompt's rule 1 is not strong enough. Tighten the wording of rule 1 and rerun step 3 before committing.

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/reviewer.md recon/dryrun recon/PROMPT_CHANGELOG.md recon/RUNLOG.md
git commit -m "Add reviewer agent definition and dry-run proposal"
```

---

### Task 5: On-clock runbook

**Files:**
- Create: `recon/RUNBOOK.md`

**Interfaces:**
- Consumes: the dispatch prompt variables of all three agents.
- Produces: the exact sequence the orchestrator follows once the clock starts. This is also what the demo walks through.

- [ ] **Step 1: Write the runbook**

```bash
cd "/Users/sauravroy/Desktop/LATER OA"
cat > recon/RUNBOOK.md <<'EOF'
# Recon runbook (on-clock)

The clock starts at step 1. Record it: `echo "- $(date -u +%FT%TZ) | ORCH | clock=start | outcome=ok | Round one dispatched" >> recon/RUNLOG.md`

Between every step the orchestrator reads the outputs before dispatching the next tier. Hand corrections are logged as `ORCH` lines.

## Step 1 — Round one (four probers in parallel, ~5 min)

Dispatch all four in one message. Each uses `subagent_type: "prober"`. Common footer for every prompt:

```
ROUND: 1
BASE_URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Working directory: /Users/sauravroy/Desktop/LATER OA
Follow the full protocol.
```

| SLICE | ENDPOINTS | OUTPUT |
|---|---|---|
| read | GET /api/v1/health, GET /api/v1/proj, GET /api/v1/proj/ | recon/round1/read.md |
| write | POST /api/v1/proj/new, PUT /api/v1/proj/modify, POST /api/v1/proj/touch | recon/round1/write.md |
| remove | DELETE /api/v1/proj/remove | recon/round1/remove.md |
| items | GET /api/v1/proj/items, POST /api/v1/proj/items/add, POST /api/v1/proj/items/mark, DELETE /api/v1/proj/items/yank | recon/round1/items.md |

Extra line for the `read` prompt: `You may not create projects. If the list is empty, record that and move on.`
Extra line for the `remove` prompt: `Create at least two fixtures so you can test removing an existing id and then removing it again.`

Check: `ls recon/round1 && tail -4 recon/RUNLOG.md`. Four findings files, four prober lines. If one is missing, proceed anyway and note it as an `ORCH` line.

## Step 2 — Synthesize (~3 min)

`subagent_type: "synthesizer"`:

```
INPUT_DIRS: recon/round1
NOTES_OUTPUT: API_NOTES.md
UNRESOLVED_OUTPUT: recon/unresolved.md
ROUND: 1
Working directory: /Users/sauravroy/Desktop/LATER OA
```

Read both outputs. If the notes contradict a raw finding, fix the notes by hand and add an `ORCH` log line saying what and why.

## Step 3 — Review and rewrite (~2 min)

`subagent_type: "reviewer"`:

```
FINDINGS_DIR: recon/round1
UNRESOLVED: recon/unresolved.md
PROBER_PATH: .claude/agents/prober.md
REWRITE_OUTPUT: recon/round1/prober.proposed.md
ROUND: 1
Working directory: /Users/sauravroy/Desktop/LATER OA
```

Then:
```bash
diff .claude/agents/prober.md recon/round1/prober.proposed.md
tail -40 recon/PROMPT_CHANGELOG.md
```
Accept: `cp recon/round1/prober.proposed.md .claude/agents/prober.md && git add -A && git commit -m "Reviewer rewrite of prober after round 1"`.
Reject: leave the file, add an `ORCH` log line with the reason. Either way is demo material.

## Step 4 — Round two (~4 min)

Read `recon/unresolved.md`. Group the endpoint sections into two or three slices. For each, `subagent_type: "prober"`:

```
SLICE: r2-<name>
ENDPOINTS: <endpoints from the group>
OUTPUT: recon/round2/<name>.md
ROUND: 2
BASE_URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Working directory: /Users/sauravroy/Desktop/LATER OA
Round 2 mode: answer only the questions below, in order, then clean up.
<paste the numbered items for this group>
```

## Step 5 — Finalize (~2 min)

`subagent_type: "synthesizer"`:

```
INPUT_DIRS: recon/round1, recon/round2
NOTES_OUTPUT: API_NOTES.md
UNRESOLVED_OUTPUT: recon/unresolved.md
ROUND: 2
Working directory: /Users/sauravroy/Desktop/LATER OA
```

Commit: `git add -A && git commit -m "Final API notes after two recon rounds"`.

## Step 6 — Hand off

Agents are done. Build `projects_client.py` and the persona surfaces directly, per `HANDOFF.md` from the 15 minute mark. Whatever is still in `recon/unresolved.md` goes into `DECISIONS.md` as known unknowns.
EOF
```

- [ ] **Step 2: Verify**

Run: `grep -c 'subagent_type' recon/RUNBOOK.md`
Expected: `5` or more (one per dispatch step).

- [ ] **Step 3: Commit**

```bash
git add recon/RUNBOOK.md
git commit -m "Add on-clock recon runbook"
```
