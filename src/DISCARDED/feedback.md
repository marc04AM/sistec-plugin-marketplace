a cosa serve? usa la plan mode nativa che fa esattamente la stessa cosa

---
description: Triage an attached screenshot and/or written feedback — observe, diagnose, then propose a fix for approval before applying.
---

The user invoked `/feedback` with a **screenshot and/or written feedback** about something
that happened (an error, unexpected UI, a launch/test result, a bug, a surprising prompt,
etc.). This is a **general triage** command — it is not tied to any one feature.

Work through these steps and **do not change anything until the approval gate (step 4)**:

1. **Examine the evidence — and save it.** Read every attached image carefully — window
   titles, terminal output, error text, dialogs, pickers, permission prompts, exit codes,
   highlighted regions — plus any written feedback. State concisely **what you observe**
   (don't guess past what's visible). **Save any attached screenshot(s)** to
   `commands\feedback\resources\` (or, when the feedback is about a specific project, that
   project's `external resources\`) with a dated name, so the evidence is preserved and can be
   referenced from the ledger entry (step 6).

2. **Understand actual vs expected.** Use the active project, recent session context, and
   recalled memory to interpret what *should* have happened versus what did. Read the
   relevant files **read-only** to confirm — do not edit while investigating.

3. **Diagnose the root cause.** Be specific: name the exact file / line / setting / command
   responsible. If the evidence shows success (nothing wrong), say so plainly, then skip to the
   log (step 6) and stop — no fix is proposed.

4. **Propose a fix and ask for approval — APPLY NOTHING YET.** Present the exact change(s)
   and where they go, then gate on `AskUserQuestion` with options **`Proceed`** / **`Revise`**.
   - If the fix touches `.claude\*` (commands / settings / agent config) note it is
     **agent-config self-modification** and needs explicit authorization.
   - If it needs a **permission rule**, hand the user the exact rule to paste (self-editing
     the permissions allow-list is blocked) — and prefer a fix that needs **no** new
     permission.
   - On **`Revise`** → refine the proposal and re-ask; still apply nothing.

5. **On `Proceed`, apply** the change(s) and report the result faithfully (including anything
   that didn't work). If the fix is declined / abandonedma s at the gate, apply nothing.

6. **Log every triage — always.** Whatever the outcome — **fix applied**, **no fix needed**
   (step 3 success), or **fix declined** — append request + result to the **active project's**
   ledger (`<project>\<project>.log.md`), or to `_config\config.log.md` for governance/config
   items. State the outcome explicitly and **reference the saved evidence path** from step 1.
