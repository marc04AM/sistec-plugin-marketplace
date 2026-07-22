---
name: csharp-doc-comments
description: >-
  Writes, fixes, and audits C# XML documentation comments (///) and inline
  comments in .NET solutions, applying Microsoft conventions (dotnet-api-docs
  wording, StyleCop SA16xx) with automatic adaptation to the host project's
  rules. Use whenever C# code is written, edited, reviewed, or documented:
  adding summary, param, returns or exception tags, documenting classes,
  methods, properties, records or interfaces, fixing CS1591 or SA16xx
  warnings, auditing documentation coverage, documenting only the changed set
  (the diff vs HEAD), writing inline why-comments, or producing
  README/architecture docs for a .NET solution. Trigger on "document",
  "add comments", "XML docs", "doc comments", "add doc comments", "document
  this", "summary", "commenta", "documenta", or any work on .cs files — even
  when documentation is not explicitly requested.
license: MIT
metadata:
  version: "1.1.0"
---

# C# Doc Comments

Produce verified, Microsoft-conformant documentation for C#/.NET code at minimum token cost. Not for non-.NET languages (use a language-specific skill).

## First principle — two readers

- XML `///` docs describe the **contract for callers**: what a member does, parameters, return, exceptions. Callers read them in IntelliSense without seeing the body.
- Inline `//` comments explain **why** for **maintainers** of the body.

Never mix the duties: no implementation detail in `<summary>`, no contract restatement in `//`.

## Step 0 — Adapt to the host project (once per session)

1. Look for doc conventions before applying defaults: `.editorconfig` (`dotnet_diagnostic.SA16xx` / `CS1591` severities), `stylecop.json`, `CLAUDE.md`, `.claude/rules/*` (doc-related sections only), and one neighboring well-documented `.cs` file.
2. Host conventions override the defaults below. In a Sistec repository (AsyncPayload, OPC UA, HMI/PLC), also read `references/sistec.md`.
3. Note whether any `.csproj` sets `GenerateDocumentationFile` — if so, `dotnet build` is the validation gate.

## Mode dispatch

- **Mode A — inline (default).** While writing or editing any C# code, apply the Core rules below. Load a reference file only for a case the rules don't cover (Load-when table).
- **Mode B — documentation pass.** The user asks to document/audit files or a project, or to fix doc warnings. Resolve scope first (below), then follow the Workflow.

## Scope — what to document (Mode B)

- **A path** (project / solution / folder) → every applicable type and member under it.
- **The changed set** → only the `.cs` files changed vs `HEAD` (staged + unstaged, tracked + untracked). List with `git status --short`, keep paths ending `.cs`, skip generated output (`bin/`, `obj/`, `*.g.cs`; include `*.Designer.cs` only when it is itself changed). Within them document only the **touched** types and members, widening to a caller or dependency only when a doc there clarifies the change.
- **Specific places** → when the user points at particular types / members / lines, document exactly those.
- **Code just written or modified** → Mode A already covers it: document as part of the edit; never leave freshly written public/protected surface undocumented.

A bare "document this" with no path and nothing pointed at defaults to the **changed set**. If the changed set is empty, report "no changed `.cs` to document" and stop. If the tree isn't a git repo (or has no `HEAD` yet), the diff doesn't apply: ask for an explicit path, or fall back to the tracked `.cs` under the current folder.

Editing the working tree is enough — leave the edits unstaged for review; don't `git add`.

## Core rules

XML documentation:

1. `<summary>` on every public and protected type and member. One sentence, third-person present verb ("Gets…", "Converts…", "Represents…"), ends with a period, adds information beyond the member name — lead with the purpose (what it is for), add mechanism, units, ranges, or edge cases only when they clarify.
2. Fixed openers — constructor: "Initializes a new instance of the `<see cref="X"/>` class." (struct: "… struct."); property: "Gets or sets X." / "Gets X."; bool property: "Gets or sets a value indicating whether X."; event: "Occurs when X."; enum type: "Specifies X."; interface: "Defines X."; exception class: "The exception that is thrown when X."; abstract/virtual: "When overridden in a derived class, X."
3. `<param>` for every parameter; `<returns>` on every non-void method; `<typeparam>` per generic parameter. Fill, don't strip: never leave a tag empty, rewrite a vague or name-echoing one, delete a `<param>` only when its parameter is gone from the signature. Bool parameter: "`true` to X; otherwise, `false`." Bool return: "`true` if X; otherwise, `false`." `out` parameter: "When this method returns, contains X. This parameter is treated as uninitialized."
4. `<exception cref="…">` only for exceptions verifiably thrown in the body, or documented on a member the body directly calls and that has been read. State the condition directly ("`<paramref name="x"/>` is `<see langword="null"/>`."), never "Thrown if…".
5. Overrides and interface implementations: write `<inheritdoc/>` explicitly — IDE auto-inheritance never reaches the compiled XML file. When the override changes or specializes behavior, keep `<inheritdoc/>` and add only the tags that differ (e.g. `<inheritdoc/>` plus a custom `<returns>` on a `ToString` override); never retype the whole block.
6. Prefer `<see cref="Member"/>`, `<see langword="null"/>`, `<c>code</c>` over plain-text names. Generic cref uses braces: `cref="List{T}"`.
7. Records and primary constructors: `<param>` tags on the type declaration document positional parameters. Partial types: put the doc block on the primary declaration only.
8. Enums: the type `<summary>` states the purpose and does not enumerate the members; each enum member gets its own `///` summary.
9. Add an `<example>` (with `<code>`) or `<remarks>` block when a short sample materially helps a caller — a non-obvious argument combination, a required call order, a subtle default. Skip it where summary + signature already make usage obvious.
10. Form: `<summary>`, `<remarks>`, and `<example>` stay in expanded multi-line `///` form (open tag, text, close tag each on its own line); one tag per line for the rest. Never collapse an existing expanded block — it keeps line diffs readable and matches what doc analyzers and formatters expect.
11. Private/internal members: `<summary>` only when the name does not already state the intent (host rules may override). A public member of a private type is effectively private — judge it as private. Exception: a serialization/wire/DTO contract (JSON shape, discriminator) is documented even on a private type.
12. Test classes and test methods: no XML docs — the test name is the documentation (host rules may override).

Inline comments:

13. Write a `//` comment only if it passes the gate: not obvious from the code → not fixable by a better name → explains WHY (constraint, workaround + issue link, invariant, performance, concurrency) → useful to a future maintainer. If it only restates WHAT, do not write it. Never narrate intent ("changed to…", "now uses…") and never encode out-of-context facts (log findings, ticket numbers, dated notes) — those belong in reports/issues, not source.
14. Own line, capital first letter, one space after `//`. Deferred work: `// TODO(owner): action — context` (Visual Studio Task List tokens: TODO, HACK, UNDONE).
15. Reference constants and symbols instead of duplicating their values in prose — duplicated values drift.
16. Default volume is the fewest comments that pass the gate. Unconstrained generation over-comments (~2× human baseline); restraint is part of the deliverable.

Hard rules (both modes):

- Never document behavior not verified in the code being read. No invented defaults, exceptions, value ranges, or thread-safety claims — a flagged gap is correct, a guess is a defect.
- When something cannot be verified cheaply, write `<see cref="…"/>` to the authoritative member, or flag "see source at File.cs:line", or ask.
- A documentation edit never changes executable code. If the code itself needs fixing, report it; do not fix it silently inside a doc pass.

## Mode B — documentation pass workflow

Copy this checklist into the response and tick it:

```
Doc pass:
- [ ] 1. Scope — resolve per "Scope — what to document" (path / changed set / specific places).
- [ ] 2. Scan — python scripts/doc_coverage.py <path> [--stats] [--exclude Tests]; treat output as a candidate list, not ground truth.
- [ ] 3. Document — per candidate: read only that declaration and its body, then write tags per Core rules (wording.md / tags.md as needed). Batch all edits to one file together.
- [ ] 4. Validate — if GenerateDocumentationFile is set: dotnet build, fix every CS1591/CS1572/CS1573/CS1734/CS0419, rebuild until clean. Otherwise re-run the scan and confirm zero candidates and tag/signature match.
- [ ] 5. Review — re-read the diff once: every sentence verifiable? any WHAT-restating comment? any invented fact? Fix before reporting.
- [ ] 6. Report — documented / skipped / flagged counts, coverage before → after (--stats), gaps with file:line.
```

Do not read whole files to find gaps — that is the scanner's job (script source never enters context, only its output). The script requires Python 3, standard library only.

## Load-when table

| Read | When |
|---|---|
| `references/wording.md` | Writing summaries/params/returns beyond the fixed openers: operators, events/EventArgs, async methods, enum members, overloads, Dispose, `<value>`, exception phrasing detail |
| `references/tags.md` | Choosing between tags, `<inheritdoc/>` pitfalls, records/primary constructors, compiler doc warnings (CS15xx/CS0419) |
| `references/inline-comments.md` | Judgment calls on inline comments; auditing or rewriting existing comments |
| `references/project-docs.md` | Asked for README / architecture / solution-level documentation |
| `references/sistec.md` | Working inside a Sistec repository |

## Red flags — stop when caught thinking

- "The build will probably pass; no need to run it."
- "It surely throws ArgumentNullException; everyone does." (verify or omit)
- "More comments are safer."
- "I'll paraphrase the member name as the summary."
- "It's private, skip it" / "It's public, restate the name" — both wrong by default.
- "The whole project needs documenting; I'll read every file." (run the scanner)
- "Nothing was pointed at, so I'll document the whole folder." (a bare "document this" defaults to the changed set vs HEAD)
