# Sistec house conventions (wired module)

Authoritative source: `.claude/rules/naming-style.md` §Commenting Style (verified 2026-07-17). These rules extend the Microsoft defaults; where they differ, they win inside Sistec repositories.

## XML documentation (naming-style.md:114–138)

- Mandatory on **all** public and protected members — no exemptions for "obvious" members.
- `<summary>`: one sentence. The rule file's own example uses third-person present ("Calculates the discounted price…"), consistent with Microsoft wording — follow the example.
- `<param>`: mandatory for **every** parameter; state purpose and valid range.
- `<returns>`: mandatory on every non-void method; describe the return value **and edge cases** ("…or zero if the line is invalid").
- `<exception>`: **list every exception the method can throw, with its condition.** Stricter than the general default — during a doc pass on Sistec code, trace throw sites before declaring the docs complete.
- `<remarks>`: only for non-obvious behavior, algorithms, or business rules.
- Internal/private members: `<summary>` only, and only when intent is not self-evident from the name. (The older `add-doc` skill says "never document private/internal" — the rules file wins.)
- `<inheritdoc/>` to inherit documentation.
- **Direction annotation** on OPC/PLC-adjacent members: `/// <remarks>HMI -> PLC</remarks>` marks communication direction. Domain metadata, not prose — preserve it verbatim; never strip or "improve" it; add it when documenting new tag members whose direction is known from the tag configuration.

## Inline comments (naming-style.md:140–156)

- Minimize; only WHY, never WHAT.
- The house example: a justification comment above a deliberately empty `catch` — comments exist to make intentional-looking-wrong code safe.
- Multi-step hardware protocol: `// STEP 1:` / `// STEP 2:` numbered comments.
- **English only** — comments, identifiers, public APIs, technical documentation (naming-style.md:156). Spec/engineering documents produced by `spec-document` may be Italian; code never.

## Domain phrasing

- `AsyncPayload<T>` is a well-known type: methods returning it document the success value and the failure semantics briefly ("…or a failed payload when the session is closed") and link `<see cref="AsyncPayload{T}"/>` — never re-explain the struct per call site.
- Summaries state a **domain capability**, not a procedural transfer: "Applies the configured discount policy to the order line." — not "Copies fields from source to destination." If the only accurate summary sounds procedural (`CopyJobDataFields`-style), the code violates the house anti-procedural rule — document it accurately and **flag the smell** in the report; never embellish.
- Tag-subscription members (`Device : TagProviderBase<T>`): summaries describe the tag's meaning in the machine/process, `<remarks>` carry direction and PLC structure-layout constraints ("order matters: matches the CODESYS structure").
