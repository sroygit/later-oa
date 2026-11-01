# Recon runbook (on-clock)

The clock starts at step 1. Record it: `echo "- $(date -u +%FT%TZ) | ORCH | clock=start | outcome=ok | Round one dispatched" >> recon/RUNLOG.md`

Between every step the orchestrator reads the outputs before dispatching the next tier. Hand corrections are logged as `ORCH` lines.

## Dispatch mechanism

Preferred: Agent tool with `subagent_type: "<prober|synthesizer|reviewer>"`.

Fallback (needed when the session started before the definitions existed, since agent types load at session start): Agent tool with `subagent_type: "general-purpose"`, `model` set from the definition's frontmatter (`sonnet` or `fable`), and the prompt built as:

```
You are operating under the following agent definition. Follow it exactly. You may only use <tools from frontmatter>.

=== AGENT DEFINITION (.claude/agents/<name>.md) ===
<body of the file, frontmatter stripped>

=== DISPATCH ===
<the dispatch block below>
```

Print a body with: `sed '1,/^---$/{/^---$/!d;}' .claude/agents/<name>.md | sed '1,/^---$/d'`

Always read the definition file fresh at dispatch time. After the reviewer rewrites `prober.md`, round-two probers must get the new body.

## Step 1 — Round one (four probers in parallel, ~5 min)

Dispatch all four in one message. Common footer for every dispatch block:

```
ROUND: 1
BASE_URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Working directory: /Users/sauravroy/Desktop/LATER OA (use absolute paths when writing files)
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

Synthesizer dispatch block:

```
INPUT_DIRS: recon/round1
NOTES_OUTPUT: API_NOTES.md
UNRESOLVED_OUTPUT: recon/unresolved.md
ROUND: 1
Working directory: /Users/sauravroy/Desktop/LATER OA
```

Read both outputs. If the notes contradict a raw finding, fix the notes by hand and add an `ORCH` log line saying what and why.

## Step 3 — Review and rewrite (~2 min)

Reviewer dispatch block:

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

Read `recon/unresolved.md`. Group the endpoint sections into two or three slices. Prober dispatch block for each:

```
SLICE: r2-<name>
ENDPOINTS: <endpoints from the group>
OUTPUT: recon/round2/<name>.md
ROUND: 2
BASE_URL: https://fde-takehome-projects-api-hkbn2zj27a-ue.a.run.app
Working directory: /Users/sauravroy/Desktop/LATER OA (use absolute paths when writing files)
Round 2 mode: answer only the questions below, in order, then clean up.
<paste the numbered items for this group>
```

## Step 5 — Finalize (~2 min)

Synthesizer dispatch block:

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
