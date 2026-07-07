a cosa serve? scan LLM dell'intera codebase = spreco enorme che satura il contesto; il dead code lo trovano linter/analyzer (Roslyn IDE0051/CS0169, ReSharper) in modo deterministico e corretto. la sua stessa caveat ("name-based, cieco a reflection/DI, candidato non conferma") lo ammette

---
description: Heuristically find unreferenced (dead) C# types across a solution's repos — name-based scan flagging every type whose name is referenced nowhere outside its own declaration, optionally cross-checked against a sister solution to split candidates into used-there / dead-in-both / this-only, with risk tags. READ-ONLY: reports candidates, never deletes (deletion stays the user's call). Usage: /deadcode [--scope|-s "<.sln or folder>"] [--cross "<sister .sln/.slnx>"] [--out <report>]
---

The user invoked **`/deadcode`** to find **unreferenced (dead) C# types** across a multi-repo
solution and report them for review. Distilled from the panel-tracking R28–R29 procedure.
**READ-ONLY** — it produces a report and **never deletes** (deletion is the user's call, after
reviewing the heuristic + risk tags).

Constants:
- Work dir: `C:\Users\Sistec 23\source\repos\Claude`

## 1. Parse
- `--scope` / `-s "<path>"` (also accepts the deprecated `-fn`/`--fn`, hidden from `-h` help) — optional: a `.sln` or folder. Given-but-nonexistent → usage + stop.
- `--cross "<path>"` — optional sister solution (`.sln`/`.slnx`) to cross-check against.
- `--out "<path>"` — optional report path (default below).
- (`-h`/`--help` is the universal P11 help — handled by the directive, not here.)

## 2. Resolve target & repo set
Reuse the **`/gitize` Step 1–2** resolution: no `--scope` → active project's solution from its ledger;
`.sln`/folder → repo set via the `git-repos-<stem>` cache (discover + persist if absent);
project-file/`.sln`-less path → the single enclosing repo. None resolves → usage + stop.

## 3. Build the type → declaration map
Enumerate every `.cs` under the repo set, **excluding generated/output** (`**/bin/**`, `**/obj/**`,
`*.g.cs`, `*.g.i.cs`, `*.Designer.cs`, `*.AssemblyInfo.cs`). For each, collect **type declarations**
— `class` / `struct` / `record` / `interface` / `enum` / `delegate` — capturing each type **name** →
the set of files that declare it (a `partial` type spans several files; record them all).

## 4. Heuristic dead-type scan
For each declared type name, count references to that name **anywhere in the solution's `.cs` set
outside its own declaring file(s)** — a word-boundary match (`\b<Name>\b`). A type with **zero**
external by-name references is a **candidate** (heuristically dead). Notes:
- A `partial` type counts a reference only if it is outside **all** of its declaring files.
- Ignore matches inside comments only when trivially separable; otherwise keep them (false-negative
  bias is safer than deleting live code).
- This is **name-based**: see the caveat in Step 7.

## 5. Cross-check against a sister solution (`--cross`)
If `--cross` is given, parse the sister **solution file** for its **project list** (`.sln` project
lines / `.slnx` `<Project>` entries) and scan **only those projects' folders** (not the whole sibling
repo tree — the R29 refinement). For each 5309 candidate, classify:
- **USED_IN_SISTER** — referenced by name in the sister's projects → **KEEP** (a shared lib the sister
  consumes; deleting it would break the sister).
- **dead-in-both** — present but unreferenced in the sister too.
- **THIS-ONLY** — absent from the sister entirely.
Without `--cross`, every candidate is simply "unreferenced in this solution".

## 6. Risk tags
Tag each candidate to guide the review:
- `<EXT>` — a `static` class of extension methods (called via the extended type, not by class name —
  high false-positive risk).
- `<WINFORMS>` — a `Form`/`UserControl`/designer-coupled type (may be referenced from `.resx`/designer).
- `<MARK>` — a marker/blocker partial (e.g. `_FormViewBlocker`).
- `<REFLECTION-RISK>` — name appears in a non-`.cs` artifact (`.csproj`, `.resx`, `.xaml`, `.json`,
  DI registration) — flag if a quick check finds it, since reflection/DI defeats the by-name scan.

## 7. Report (read-only)
Write a Markdown report (`--out`, else the active project's
`reports\deadcode.<solution-stem>.md`): a candidate table (type, declaring file, category from
Step 5, risk tags) + per-category totals + the **caveat**, stated explicitly:

> Heuristic, **name-based** — blind to references via reflection, dependency injection, string keys,
> `.csproj`/`.resx`/`.xaml`, or runtime type resolution. A flagged type is a **review candidate, not
> a confirmed-dead deletion.** Verify before removing.

- **Never edit or delete source.** If the user later removes files, that is a separate explicit
  action (and re-running `/deadcode` will catch any **newly-orphaned** types the deletions expose —
  the R29 effect). Log to the active project ledger if one is active (P2).
