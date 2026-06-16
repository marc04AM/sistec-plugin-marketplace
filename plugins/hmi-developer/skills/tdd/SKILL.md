---
name: tdd
description: Orchestrate the Red→Green→Refactor cycle for a C# task. Writes the failing test first, confirms it fails for the right reason, writes minimum production code, verifies green, then refactors. Use when starting any new feature, bug fix, or behaviour change in the Sistec.HMI solution.
---

# TDD Cycle Orchestrator

Executes the full Red→Green→Refactor cycle for the current task. Enforces `tdd-verification.md` workflow rules (§2 Test-First Gate, §4 Sandbox Spike, §5 Run & Verify).

**Input**: Task description (inferred from conversation if omitted). Optionally: `--spike` to enter sandbox spike mode before writing the real test.

---

## Step 1 — Resolve project names

Locate the `.sln` file and the `*.Tests.csproj`:

```bash
Get-ChildItem -Recurse -Filter "*.sln" | Select-Object -First 1
Get-ChildItem -Recurse -Filter "*.Tests.csproj" | Select-Object -First 1
```

If multiple solutions exist, ask the user which one to target.

---

## Step 2 — Baseline build

Confirm the solution compiles clean before touching anything:

```bash
dotnet build <Solution>.sln --no-incremental
```

On build failure: stop, report errors, do not proceed until clean.

---

## Step 3 — Sandbox Spike (conditional)

Trigger: `--spike` flag passed, OR the task involves an unfamiliar API (OPC UA, Dapper, Modbus, KUKA), risky LINQ/async mechanic, or non-obvious math.

1. Create a throwaway `*.Spikes` console project or xUnit project — never inside a production project.
2. Write the minimum code to answer **one specific question** about the API/mechanic.
3. Run it, observe the result.
4. Discard the spike project.
5. Promote the verified behaviour into the real locked test in Step 4.

Skip this step if the mechanic is well-understood.

---

## Step 4 — RED: Write the failing test

In `<Project>.Tests`, write the test(s) that encode the prompt's exact inputs and expected outputs:

- One test per distinct behaviour; one additional case per guard clause.
- Follow `tests.md` naming: `<Method>_<Scenario>_<ExpectedOutcome>`.
- Use AAA structure. Assert on specific values from the prompt — not just `IsSuccess`.
- Do **not** write any production code yet.

Run the tests to confirm red:

```bash
dotnet test <Project>.Tests.csproj --no-build -- --filter "<TestClass>"
```

**Expected output:** all new tests fail. If a new test passes without production code, the test is wrong — fix it before continuing.

Report the failure reason (not just exit code): confirm it fails because the implementation is missing, not due to a compile error or wrong assertion.

---

## Step 5 — GREEN: Write minimum production code

Write only the code needed to make the locked tests pass:

- No extra behaviour, no speculative logic, no "while I'm here" improvements.
- Follow `architecture.md` layer boundaries — no shortcuts.
- Follow `csharp-idioms.md`: no procedural loops, no static utility bags, no anemic models.

Run the full test suite:

```bash
dotnet build <Solution>.sln && dotnet test <Project>.Tests.csproj
```

**Expected output:** all locked tests green, no previously-passing tests regressed.

On failure: fix production code only — never touch the test. Re-run. Repeat until green.

---

## Step 6 — REFACTOR

With all tests green, remove duplication and restore OOP/functional/DDD shape:

- Apply `design-patterns.md` patterns where appropriate.
- Eliminate procedural code introduced during Green (imperative loops → LINQ, static helpers → owned methods, etc.).
- No behaviour change — tests must stay green.

Re-run after every non-trivial refactor step:

```bash
dotnet test <Project>.Tests.csproj
```

---

## Step 7 — Definition of Done

A change is **done** only when all of the following hold:

- [ ] `dotnet build` exits clean (0 warnings promoted to errors, 0 errors)
- [ ] Every locked test passes
- [ ] Each test's actual output matches the **starting parameters and expected output** from the prompt — not just exit code
- [ ] No previously-passing test regressed
- [ ] No `architecture.md` boundary violation introduced
- [ ] No mock used that `tests.md` does not permit

Report the final test run output verbatim (counts, duration, pass/fail per test name).

---

## Output Format

```
## TDD Cycle: <task description>

### Baseline
Build: CLEAN | <N errors>

### Red
Tests written: <list>
Run result: <N> failed (expected) — reason: <why each fails>

### Green
Production code: <files changed>
Run result: <N> passed, 0 failed

### Refactor
Changes: <description>
Run result: <N> passed, 0 failed

### Done
[x] Build clean
[x] All locked tests green
[x] Results match prompt expectations
[x] No regressions
[x] No boundary violations
```
