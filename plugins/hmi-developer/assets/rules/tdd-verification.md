---
paths:
  - "**/*.cs"
  - "**/*.csproj"
  - "**/*.sln"
---

## Fidelity & Locked-Test Contract

Always-on guardrails for `.cs` work. Workflow execution (Red→Green→Refactor, spike, run & verify) is in `/tdd` skill.

### 1. Prompt & Data Fidelity

- The prompt and the supplied data are the immutable spec. Implement exactly what was asked — never widen, narrow, "improve", or reinterpret it.
- Never invent or alter input data, parameters, method signatures, types, or file contents. Unknown shape ⇒ read the real source (e.g. `PopLogic.cs`); never assume it.
- Every assumption, hypothesis, and plan step is proven against the prompt and the real code it touches, cited `file.cs:line`. Unverified ⇒ stop and verify before writing code.
- Counter-proof rule: for each conclusion, state what would falsify it, then confirm the real code/data does not.

### 2. Locked-Test Contract

Tests are a contract, not scratch work.

- **DO NOT** weaken, delete, skip, comment out, or rewrite a test to make failing code pass.
- A red test means the **production code** is wrong — fix the code, re-run, repeat until green.
- A test changes only when the **prompt's requirement itself** changes; such a change is called out explicitly in the `claude-archive` note with the reason.
- Follow the tests to the letter: the asserted expected values are the target, not a suggestion.
