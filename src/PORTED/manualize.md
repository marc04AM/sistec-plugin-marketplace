ported in maintain-manual

---
description: Maintain a Word (.docx) user manual via python-docx — port external/working-copy edits (incl. hidden comment/tracked-change channels), copy-edit (typos/grammar/style), audit against the software & insert missing functions in-style, fix structure (blank-runs→page-breaks, numbering/indent), or add "controllare" review comments. Always edits a version-bumped COPY (master untouched) after a scratchpad backup; preserves images/bold-labels/TOC. Usage: /manualize [-fn "<manual.docx>"] (--port "<ext.docx>" | --copyedit | --audit [--code "<.sln>"] | --style | --comments)
---

The user invoked **`/manualize`** to maintain a Word `.docx` user manual. Distilled from the
5315-user-manual workflow (R5–R13). It **always works on a version-bumped copy** (the master /
source `.docx` is never edited), takes a **scratchpad backup first**, and uses **python-docx**
(NOT Word-COM — COM automation hangs and corrupts `Normal.dotm`; R7). Every mode preserves the
**image count**, **bold labels**, and sets `<w:updateFields/>` so Word refreshes the TOC on open.

Constants:
- Tooling: **python-docx 1.2.0** (Word-free). Write ad-hoc helper scripts to the scratchpad dir.
- Scratchpad: the session scratchpad (backups + helper scripts go here).

## 1. Parse
- `-fn` / `--fn "<manual.docx>"` — the target manual to update. Given-but-nonexistent → usage + stop.
- Exactly **one mode** (required):
  - `--port "<external.docx>"` — port the external/working copy's incremental edits into the manual.
  - `--copyedit` — typos / grammar / readability / style-consistency pass.
  - `--audit` — consistency vs the software; insert missing functions in-style. Optional `--code "<.sln>"`.
  - `--style` — structural/style fixes (blank-run → page break, numbering/indent, multi-space).
  - `--comments` — add "controllare" review comments.
- No mode, or more than one → print usage and **stop**. (`-h`/`--help` is the universal P11 help.)

## 2. Resolve the target manual
- `-fn` given → that file.
- **No `-fn`** → the **newest `*.docx` working copy in the active project** (e.g. `external resources\`
  — never a `D:\…` master). None found → usage + stop.
- Identify the version token in the name (e.g. `V1.7`); the output is the **next** version
  (`V1.8`) in the **same project folder** — never overwrite the input. A non-versioned name → append
  `_manualized`.

## 3. Backup + bump (always, before editing)
Copy the resolved manual to the scratchpad as `<stem>_pre-<mode>.docx` (the recovery point), then
copy it to the **new version** path (Step 2) — all edits land on the new version. **Record the image
count** of the input (verify it is unchanged at the end).

## 4. Approval gate
`AskUserQuestion` (`Proceed`/`Cancel`): recap the **target manual**, the **mode**, the **new version
path**, and the backup path. On `Cancel` → stop.

## 5. Run the mode (python-docx, on the new version)

**`--port "<external.docx>"`** — diff the external copy against the manual and merge **its**
incremental edits while keeping the manual's own prior changes:
- Diff body text **and the hidden channels a text-diff skips** — **Word comments**, **tracked
  changes**, **text boxes** (R9: a review comment lived only in the comments channel).
- Isolate edits present in the external but not the manual (EXT-not-in-mine). Merge via **run-level /
  cross-run** replacement so **bold labels are preserved** (R10).
- **Do not revert the manual's deliberate edits** (e.g. a `Terminated→Cancelled` correction stays;
  a resolved comment stays resolved). If an external "edit" is actually stale (already handled),
  skip it and say so.

**`--copyedit`** — in place on the new version, structure/images/tables preserved:
- Fix typos, grammar, readability; collapse redundant phrasing. Enforce **style consistency** —
  remove orphan styles (map `Body Text*`/`Stile1` → `Normal`/`Numerato`, mismatched cells → the
  sibling style), fix **duplicate headings**. Watch the **cp1252/utf-8** encoding gotcha. Refresh TOC.

**`--audit [--code "<.sln>"]`** — does the manual describe every implemented function/procedure?
- Establish code ground truth: build an **HMI function inventory** from the solution (`--code`, else
  the active project's solution via the `/gitize` Step 1–2 resolution; a large inventory may be
  delegated to a read-only Explore agent). Classify the manual's coverage → **gaps** (implemented,
  undocumented) / **stale** (documented, not in code) / **implied procedures**.
- Insert the **high-value gaps** in the manual's existing style with **`Immagine:` placeholders**
  (screenshots are captured separately); fix stale wording. Track lower-value gaps in the project's
  `reports\manual_open_items.md`.

**`--style`** — mechanical structure/style fixes:
- Replace each **run of ≥3 empty body paragraphs** with a single **page break**
  (`add_run().add_break(WD_BREAK.PAGE)` + remove the extra empties) — but **skip a trailing
  end-of-document run** (it only adds a blank final page; offer it separately). Runs of 1–2 left.
- Fix **numbering/indent**: give inserted list items a proper `numPr` (`ilvl` + a section-matching
  `numId`, restarting per section) instead of the style default; collapse multi-space artifacts
  (`:  `, triple space) to one.

**`--comments`** — add Word review comments:
- `Document.add_comment(runs, text="controllare", author="Revisione", initials=…)` on the
  **optional procedure-heading items** and each **authored/changed block**. Don't comment mechanical
  ported edits unless asked. Note any **pre-existing user comments** (e.g. author "Andrea Biasutti")
  and keep yours under a distinct author so they're separable. Verify refs == comments (no orphans).

## 6. Report
- The new version path + the scratchpad backup path; **image count before/after** (must match — flag
  any delta and its cause); per-mode summary (edits ported / fixes applied / gaps inserted / breaks
  made / comments added). Confirm the **master/source was untouched**.
- The manuals are documents, not git source — don't stage anything. Ledger entry (P2); update
  `reports\manual_open_items.md` when `--audit` defers work.
