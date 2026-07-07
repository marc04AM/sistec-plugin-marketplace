---
name: add-doc
description: The house discipline for C# comments — XML documentation on types and their public/protected members, plus inline-comment hygiene. Consult it whenever you write or modify C# code (document the types and members you touch as part of the edit), when asked to document a project / solution / folder, when asked to add or fix comments at specific places, or when documenting just the changed set (your diff vs HEAD). Triggers on "add XML docs", "document this", "comment this code", "add doc comments" — and applies automatically to code you edit.
disable-model-invocation: false
---

Add and maintain XML documentation and inline comments on C# code: classes, records, structs, enums, interfaces, delegates and their public/protected members. This is the single comment discipline — follow it both when documenting on request and when writing or modifying code yourself.

## Scope — what to document

- **A path** (project / solution / folder) → every applicable type and member under it.
- **The changed set** → document only the `.cs` files changed vs `HEAD` (staged + unstaged, tracked + untracked). List with `git status --short`, keep paths ending `.cs`, skip generated output (`bin/`, `obj/`, `*.g.cs`; include `*.Designer.cs` only when it is itself changed). Within them document only the **touched** types and members, widening to a caller or dependency only when a doc there clarifies the change.
- **Specific places** → when the user points at particular types / members / lines, document exactly those — same rules.
- **Code you just wrote or modified** → document it as part of the edit; don't leave freshly written public/protected surface undocumented.

**Resolving scope when it's ambiguous:** a bare "document this" with no path and nothing pointed at defaults to the **changed set**. If the changed set is empty, report "no changed `.cs` to document" and stop. If the working tree isn't a git repo (or has no `HEAD` yet — initial commit), the `vs HEAD` diff doesn't apply: ask for an explicit path, or fall back to the tracked `.cs` under the current folder.

Editing the working tree is enough — leave the edits unstaged for review; don't `git add`.

## Rules

**Types**
- Document **every type declaration** — `class` / `struct` / `record` / `enum` / `interface` / `delegate`, public *and* private. A private or nested type gets a one-liner `<summary>`; an empty `<summary></summary>` is a defect.
- On **partial** types, document only the primary declaration.
- **Enums:** the type `<summary>` states the purpose and does **not** enumerate members; each member gets its own `///` summary.

**Members**
- Document **every public and protected member.** A public member of a private type is effectively private — judge it as private.
- **Don't** document private members (name them well) **except** a non-obvious contract/invariant, or a serialization/wire/DTO contract (JSON shape, discriminator) — that is documented even on a private type.

**Content**
- **Purpose first.** Lead every `<summary>` / `<param>` / `<returns>` with *what it is for* — the intent, not a restatement of the signature. Add mechanism, units, ranges, or edge cases only when they clarify. Keep it tight.
- **Params — fill, don't strip.** Give each existing parameter a meaningful, purpose-focused `<param>`: add it if missing, rewrite it if vague or echoing the name, never leave it empty. Delete a `<param>` only when its parameter is gone from the signature (an orphaned tag). Treat `<returns>` the same (drop it only on `void`). `<typeparam>` is always filled, never dropped.
- **Examples when they help.** Add an `<example>` (or `<remarks>`) block when a short sample materially helps a caller — a non-obvious argument combination, a required call order, a subtle default. Skip it where the summary + signature already make usage obvious.
- For booleans, keywords and literals prefer `<see langword="..."/>`; for references to other types or members prefer `<see cref="..."/>` over plain text.

**Form**
- **Never collapse XML doc tags onto one line** — canonical multi-line `///` form (each tag opens and closes on its own line): it keeps line diffs readable and matches what the doc analyzers/formatters expect. Don't collapse an existing expanded block.

**Inline comments**
- Simplify or delete redundant, stale, or noisy inline comments. **Never narrate intent** ("changed to…", "now uses…") and **never encode out-of-context facts** (log findings, ticket numbers, dated notes) — those belong in reports/issues, not source.
- Default to **no inline comment** where the code already speaks for itself; prefer a better name or shape over a comment. (This is about inline comments — XML doc on the public/protected surface is still required.)
