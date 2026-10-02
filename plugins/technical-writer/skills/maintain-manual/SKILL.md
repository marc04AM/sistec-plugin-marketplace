---
name: maintain-manual
description: >-
  Maintains an ALREADY EXISTING operator manual in Word (.docx) format with python-docx. Modes:
  port in the changes from a revision copy (including the hidden channels — Word comments and
  revisions/tracked-changes); copy-editing (typos/grammar/style); coverage audit against the
  software with in-style insertion of the missing features; structural fixes (runs of empty
  paragraphs → page break, numbering/indentation); or adding review comments. Use it when the
  user has an existing `.docx` manual to update, correct, revise or audit (e.g. "aggiorna il
  manuale", "correggi il manuale", "revisiona il manuale .docx") — NOT to generate a new manual
  (that is the `technical-writer` skill, which produces Markdown/HTML). Always works on a COPY
  with an incremented version (the master stays untouched), with a backup in the scratchpad, and
  preserves the image count, bold labels and TOC.
---

# Maintain Manual — maintaining a Word (.docx) manual

Maintains an **operator manual that already exists as `.docx`**. It is the counterpart of `technical-writer`:
that one **generates** a new manual (Markdown → HTML); this one **maintains** an existing Word file
(ports revision changes, corrects, audits, fixes the structure, comments). If the user wants to
*create* a manual from scratch, it is `technical-writer` — not this one.
The manual is in Italian: keep every text you write or insert into it in Italian.

**Mechanism: python-docx, NEVER Word-COM.** Word COM automation hangs and corrupts
`Normal.dotm` — do not use it. Use **python-docx** (tested on 1.2.0, Word-free) by writing ad-hoc
helper scripts in the session scratchpad.

## Invariant rules (every mode)

1. **Never touch the master.** Work on a **copy with an incremented version**: from the version
   token in the name (`V1.7`) the output is `V1.8` in the **same folder**; a name without a version →
   append `_maintained`. Never overwrite the input.
2. **Back up before editing.** Copy the resolved manual into the scratchpad as `<stem>_pre-<mode>.docx`
   (restore point), then copy it to the new version's path — all changes go there.
3. **Preserve** and **verify** the invariants: image count and heading/TOC-entry count
   (record them first, check they are unchanged at the end — report every delta with its cause);
   **bold labels** (spot-check the count of bold runs, or state that it is
   best-effort); and set `<w:updateFields/>` so Word regenerates the TOC on open.

## 1. Resolve the target manual

- `.docx` path given → that one. Non-existent → report and stop.
- No path → the **most recent** `.docx` (by modification date) in the working / project folder.
  None found → report and stop. (The most recent one might be a backup/stray: the Step 3 gate
  confirms the target before editing — it is the safety net.)
- **Open read-only to validate**: if python-docx cannot load it (corrupt file) or it is
  **locked by an open Word**, report and stop **before** any backup or edit.
- **Detect the hidden channels already present** (Word comments, unresolved tracked-changes): record them
  now; if there are any and the chosen mode is **not** `port`, ask whether to accept/reject them before editing
  (editing on top of them can tangle them badly).

## 2. Choose the mode (one at a time)

If the request implies more than one (e.g. copyedit + style), run them **in sequence**, each
on the output of the previous one, with a gate each — do not merge them into a single pass.

- **port `<external.docx>`** — ports the incremental changes of the external copy into the manual,
  keeping the changes already made in the manual:
  - diff the body text **AND the channels a text-diff skips** — **Word comments**, **revisions/
    tracked-changes**, **text boxes** (a review note may live only in the comments channel).
  - isolate the changes present in the external copy but not in the manual; apply them via **run-level /
    cross-run** replacement so the **bold labels** are preserved.
  - **do not undo** the manual's deliberate changes (a correction already made stays; a resolved
    comment stays resolved). If an external "change" is already superseded, skip it and say so.
- **copyedit** — typos, grammar, readability; remove redundancies. Normalize the **style** (map
  orphan styles onto the standard ones, fix duplicate headings). Watch out for the
  **cp1252/utf-8** encoding gotcha. Refresh the TOC.
- **audit** — does the manual describe every implemented feature/procedure?
  - build the **HMI feature inventory** from the code indicated in the conversation (`--code
    "<solution/folder>"` is the explicit shortcut), otherwise the active project's solution;
    for large inventories delegate to a read-only **Explore** agent.
  - classify the coverage → **gap** (implemented, not documented) / **stale** (documented, not in the
    code) / **implicit procedures**.
  - insert the **high-value gaps** in the manual's existing style, with `Immagine:` placeholders
    (screenshots are captured separately); correct the stale text. Track the minor gaps in a
    `manual-open-items.md` file next to the manual.
- **style** — mechanical structure fixes:
  - every **run of ≥3 empty paragraphs** → a single **page break** (`add_run().add_break(WD_BREAK.PAGE)`
    + remove the extras) — but **skip the final end-of-document run** (it would only add an empty
    page; offer it separately). Runs of 1–2 stay.
  - **numbering/indentation**: give inserted list items a correct `numPr` (`ilvl` + a `numId`
    consistent with the section) instead of the style default; collapse multi-space artifacts.
- **comments** — add Word review comments:
  `Document.add_comment(runs, text="controllare", author="Revisione", initials=…)` on the optional
  procedure entries and on the modified blocks. Note any **pre-existing user comments** and
  keep yours under a distinct author so they are separable. Check that references == comments
  (no orphans).

## 3. Approval gate

`AskUserQuestion` (`Proceed`/`Cancel`): recap the **target manual**, the **mode**, the **new
version's path** and the **backup path**. On `Cancel` → stop.

## 4. Run the mode (python-docx, on the new version)

Structure/images/tables preserved. Apply the mode chosen in step 2.

## 5. Report

- New version's path + backup path in the scratchpad.
- **Image count before/after** (must match — report every delta and its cause).
- Per-mode summary: changes ported / fixes applied / gaps inserted / page breaks made / comments
  added.
- Explicit confirmation that the **master/source was left untouched**.

## Notes

- Manuals are documents, not git source — do not stage anything.
- An `audit` mode run that defers work updates `manual-open-items.md` next to the manual.
- Running python/python-docx scripts may ask for permission the first time — the user approves
  case by case.
