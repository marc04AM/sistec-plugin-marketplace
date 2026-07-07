ported in add-doc

---
description: Apply /simplify (quality pass) to the changed code first, then add/update XML documentation comments on every type and public/protected member per DEVELOPMENT.md S9 (Comment Discipline) — purpose-first descriptions, every existing param filled, examples where helpful. Multi-repo aware; reuses the /gitize repo-set cache. Operates on the working-tree changes vs HEAD; leaves its edits unstaged (P15). Usage: /commentize [--scope|-s "<.sln, project file, or folder>"]
---

The user invoked **`/commentize`** to clean up the **changed code** — first run **`/simplify`** (the
quality pass), then add/correct its XML documentation comments per DEVELOPMENT.md **S9 (Comment
Discipline)**. This command **edits the working tree** (the simplify pass + comment text) and
**leaves its edits unstaged** (P15).

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional target: a `.sln`, a project file (`.csproj`/`.vbproj`/…),
  or a folder. If given but the path does not exist → print the usage line and **stop**.
- No other flags. (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution exactly:
- **No `--scope`** → resolve the target from the **active Claude project's ledger**
  (`<active-proj>\<active-proj>.log.md` — the `.sln` + root its work targets). If none resolves,
  print the usage line and **stop**.
- A `.sln` (or single-`.sln` folder) → **solution target**: recall `git-repos-<stem>` memory for
  the repo set, else discover (root + immediate subfolders with `.git`) and persist it.
- A project file or any `.sln`-less path → **single-repo target**: enclosing repo via
  `git -C <dir> rev-parse --show-toplevel`, scoped to that one repo (skip the repo-set cache).

## 3. Collect the changed code files
Across the resolved repo set, list the **changed code files** vs `HEAD` — both staged and
unstaged, tracked and untracked — restricted to C# source (`*.cs`):
- Per repo: `git status --short` (batch the repos in one shell pass) → keep paths ending `.cs`,
  excluding generated output (`bin/`, `obj/`, `*.g.cs`, `*.Designer.cs` is **kept** only if it is
  in the changed set — designer files rarely need doc, but treat them if the user changed them).
- If nothing changed → report "no changed code to commentize" and **stop**.

## 4. Approval gate
`AskUserQuestion` (`Proceed` / `Cancel`): recap the list of changed `.cs` files to be treated and
state the two passes, **in order**: (1) `/simplify`, then (2) the S9 XML-comment treatment. On
`Cancel` → stop.

## 5. /simplify pass (FIRST)
Invoke **`/simplify`** on the changed set (the quality cleanup — reuse, simplification, efficiency,
altitude). It applies its fixes to the working tree. **This runs before the comment pass on purpose:**
simplify may rename, restructure, merge, or remove members and change signatures, so documenting
afterwards means the XML doc describes the *final* shape (and no effort is spent documenting code
that simplify then deletes). After it completes, **re-collect** the changed `.cs` set (Step 3) so
the comment pass sees any files simplify added/changed.

## 6. XML comment pass (per changed file)
For each changed file, edit the comments **only within the changed code's scope** — the touched
types and members, widening to their callers/dependencies only when a doc clarification improves
the whole (S9's "widen it to the dependencies or callers"). Apply S9 (Comment Discipline) — the
params/returns/examples rules below are S9's own (reconciled 2026-06-26), restated here for execution:
- **Document every type declaration** (public *and* private — `class`/`struct`/`record`/`enum`/
  `interface`/`delegate`): a filled `<summary>` (a one-liner for a private/nested type). An empty
  `<summary></summary>` is a violation.
- **Document every `public` and `protected` member.** A *public member of a private type* is
  effectively private — judge it as private. **Do not** document private members (name them well)
  **except** a non-obvious contract/invariant, or a **serialization/wire/DTO contract** (JSON
  shape, discriminator) which is documented even on a private type.
- **Purpose first.** Lead every `<summary>` (and every `<param>`/`<returns>`) with **what it is
  for** — the intent, not a restatement of the signature. Add mechanism, units, ranges, or
  edge-case detail **only when it clarifies**. Keep it tight; no filler.
- **Params — fill, don't strip.** For every documented public/protected member, give **each
  existing parameter** a `<param>` with a **meaningful, purpose-focused** description — **add** it
  if missing, **update** it if vague or echoing the name; **never leave a `<param>` empty**.
  **Delete a `<param>` only when its parameter has vanished** from the signature (an orphaned tag).
  Treat `<returns>` the same — fill it meaningfully (drop it only if the method returns `void`).
  **`<typeparam>` is always filled, never dropped.**
- **Examples when they help.** Add an `<example>` block when a short usage sample materially helps
  a caller — e.g. a non-obvious argument combination, a required call order, or a subtle default.
  Skip it where the signature + summary already make usage obvious.
- **Enums:** the type `<summary>` states the purpose and must **not** enumerate the members; each
  member gets its own `///` summary.
- **Never collapse XML doc tags onto one line** — canonical multi-line `///` form (each tag opens
  and closes on its own line; single-line `<param>`/`<returns>`/`<typeparam>` each on their own
  line). Do not collapse an existing expanded block.
- **Simplify or delete** redundant, stale, or annoying **inline** comments; **never narrate intent**
  ("changed to…", "now uses…") and **never encode out-of-context facts** (log findings, ticket
  numbers, dated observations) — those belong in reports/issues/memory, not source.
- **Default to no *inline* comment** where the code already speaks for itself; prefer improving a
  name/shape over adding a comment. (This is about inline comments — XML doc on public/protected
  members is still required.)

## 7. Report & leave unstaged
- Summarize per file: the simplify changes applied, then types/members documented (params filled,
  examples added) and inline comments removed/simplified.
- **Do not `git add`/stage** any of these edits — leave them unstaged for the user's review (P15).
- Log to the active project ledger if one is active (P2).
