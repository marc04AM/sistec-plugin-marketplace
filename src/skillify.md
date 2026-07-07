---
description: Record a session and distill it into a reusable slash-command. /skillify is the recorder; its partner /skilliDo is the producer. You invoke /skillify <skill-name> with a flag spec, perform the real task once (normally, with the agent), and skillify keeps a running trace of the actions/decisions/gates; then /skilliDo generalizes that trace into a new .claude\commands\<name>.md. The executable form of DEVELOPMENT.md P0.7.e (Skill Extraction) — author a command by DOING the procedure once, not by hand. Usage: /skillify <skill-name> [<flag-spec>…] | --note|-n "<text>" | --status|-s [<skill-name>] | --abort [<skill-name>]   (distill with /skilliDo [<skill-name>])
---

The user invoked **`/skillify`** to **record this session and later distill it into a new
slash-command**. `/skillify` is the **recorder**; its partner **`/skilliDo`** is the **producer**
(skill-*ify* → skilli-*Do*). The model: you declare the new skill's **name + flags**, do the real
task once, and `/skillify` keeps a **trace** of what was actually done — the ordered steps,
branch-points, what ran automatically vs what needed confirmation, the approval gates, and the
concrete inputs that must become parameters. `/skilliDo` then **generalizes** that trace into the
finished command. This is the executable form of **P0.7.e** (Skill Extraction): author a command
by *doing* the procedure once, instead of hand-writing it via `/command new`.

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`
- Runnable command files: `.claude\commands\<name>.md`  ·  Template: `commands\commands.prompt.md`
- Per-skill recording home: `commands\<name>\` — holds `trace.md` (the live recording) and,
  after `/skilliDo`, the filled `<name>.prompt.md` (+ `resources\`).
- Doc-sync routine (used by `/skilliDo`): `.claude\commands\command.md` §3.

> A slash-command is **one-shot** — there is no on-disk watcher (Claude Code exposes no such hook).
> "Recording" is therefore **behavioral**: `/skillify <name>` arms it and writes the trace skeleton,
> and the standing directive in `trace.md` + this body tells the agent to append to the trace as the
> session proceeds. `/skilliDo` distills from that trace, reconciled against what actually happened.

## 1. Parse & dispatch
First non-flag token = **verb-or-name**. Strip surrounding quotes; flags are order-independent.
- `--note` / `-n` `"<text>"` → **add a checkpoint** (Step 3a).
- `--status` / `-s` `[<name>]` → **print the trace** read-only (Step 3b).
- `--abort` `[<name>]` → **stop recording**, keep the trace, build nothing (Step 3c).
- anything else (a bare token) → `<skill-name>` ⇒ **start recording** (Step 2).
- No argument at all → print the Usage synopsis and **stop**.
- `-h` / `--help` anywhere → **P11** prints this command's parameters and does not execute
  (handled by the directive, not here). Distillation is the **separate `/skilliDo`** command.

## 2. Start — `/skillify <name> [<flag-spec>…]`
a. **Validate `<name>`** — kebab/camel, no spaces. If `.claude\commands\<name>.md` already exists,
   say so and stop (suggest `/command edit <name>`, or pick another name). If a
   `commands\<name>\trace.md` is already armed (not yet distilled), say it's already recording and
   stop (use `--status`, or `--abort` to discard).
b. **Parse `<flag-spec>`** — the new skill's parameters, `;`-separated, each `--long -short:
   description` (e.g. `--source -s: source-solution; --dest -d: destination-solution; --purpose
   -p: purpose`). Build `(long, short, description)` rows. A spec is optional — a flagless skill
   is allowed (empty table). Note a `purpose`/`-p` value if present; it seeds the trace Purpose.
c. **Scaffold + write the trace** — create `commands\<name>\` and write `commands\<name>\trace.md`
   in the **Trace format** (below): title + today's date, **Purpose** (from the purpose flag, else
   `TBD — fill at /skilliDo`), **Declared flags** table, the **Recording directive** header, an
   empty **Trace** section, and a **Generalize-away** list (concrete values the user supplies that
   must become parameters at distillation).
d. **Arm recording.** State plainly that recording is **on**. From now until `/skilliDo` or
   `--abort`, append each **significant** action to the trace as you work: a step taken, a
   decision and *why*, a branch-point (what made it auto vs. ask), an approval gate, a reused
   sub-command/cache, and the concrete inputs to generalize. Do **not** create
   `.claude\commands\<name>.md` yet — no half-built command in the console.
e. **Confirm:** *"Recording `/<name>`. Do the task — I'll trace the steps. Run `/skilliDo` when
   finished (or `/skillify --abort` to discard)."*

## 3. Management verbs
a. **`--note "<text>"`** — append the text as a dated checkpoint line under the trace's **Trace**
   section (resolve the active recording as in Step 4a of `/skilliDo`). Use for a decision the
   agent wouldn't otherwise log, or to mark a phase boundary.
b. **`--status [<name>]`** — resolve the recording and **print** its trace (Purpose, flag table,
   the steps logged so far, the Generalize-away list). **Read-only** — writes nothing.
c. **`--abort [<name>]`** — stop recording: append a dated `aborted` end-marker line to the trace
   and report that nothing was built. Leave `commands\<name>\trace.md` in place (provenance). Do
   **not** create any runnable file.

## Trace format (`commands\<name>\trace.md`)
```markdown
# Recording: /<name>
> Armed <YYYY-MM-DD> by /skillify. Distill with /skilliDo. Status: recording.

## Purpose
<one line — the outcome the skill must produce; from -p/purpose, or TBD>

## Declared flags
| Long | Short | Description |
|------|-------|-------------|
| --source | -s | source-solution |

## Recording directive
While this trace is armed, the agent appends each significant step/decision/branch-point/
approval-gate/reused-tool to the Trace section below as work proceeds (best-effort, per turn).

## Trace
- <YYYY-MM-DD HH:MM> <step / decision / gate — and why>

## Generalize-away (concrete → parameter)
- <concrete value the user gave> → <which declared flag it becomes>
```

## Notes / constraints
- Writing `.claude\commands\*.md` is **agent-config self-modification** → the auto-mode classifier
  needs explicit per-file authorization (`[[cannot-self-edit-permissions]]`); the start path here
  writes only under `commands\<name>\`, so it does not touch `.claude\commands\`. Handle any prompt
  per **P6**; don't pre-add an allow-rule.
- The trace lives under the **recorded skill's** home (`commands\<name>\`), not the active project —
  the built command belongs to the `commands` container regardless of where the task ran.
