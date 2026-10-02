# hmi-developer

Sistec marketplace plugin for developing and maintaining the
**Sistec.HMI** solution (.NET 8 / C# 12 / WinForms). It brings the *Senior .NET
Architect* persona, the project's Clean Architecture / Clean Code rules, the
TDD cycle, and the project commands/hooks.

## Components

| Component | File | What it does |
| :-------- | :--- | :----------- |
| Skill | `skills/tdd/SKILL.md` | `/hmi-developer:tdd` — orchestrates the Red→Green→Refactor cycle in C# |
| Skill | `skills/csharp-doc-comments/SKILL.md` | Writes, fixes, and audits C# XML doc comments (`///`) and inline comments following Microsoft/StyleCop conventions (SA16xx, CS1591); on a project/solution/folder, on the changed set (diff vs HEAD), on specific places, or automatically on the code you edit |
| Skill | `skills/archive/SKILL.md` | `/hmi-developer:archive` — change summary in `.claude/claude-archive/` |
| Skill | `skills/dpi-anchor-fix/SKILL.md` | Diagnosis + fix of the .NET 8 WinForms bug "control anchored Top\|Bottom collapses to Height 0" (DPI-aware + AnchorLayoutV2 off): deterministic scanner → verdict → safe config behind a gate |
| Skill | `skills/translate/SKILL.md` | `/hmi-developer:translate` — generates the idempotent `INSERT` for `language_spv` from `MissingTranslations.csv`: exact StringName (incl. `#`), IT/EN texts inferred from the call site, placeholders preserved. Generates the `.sql` only (no DB connection). Explicit invocation (`disable-model-invocation: true`) |
| Skill | `skills/reconcile-solutions/SKILL.md` | `/hmi-developer:reconcile-solutions` — ports a feature from a SOURCE solution to a DEST one (same family on different milestone branches): git merge/cherry-pick where the repo is shared, semantic manual port where it has diverged (re-applies the *intent*, not the diff). Plans, gates, `dotnet build`, unstaged edits. Explicit invocation (`disable-model-invocation: true`) |
| Hook | `hooks/hooks.json` + `*.py` | `build-reminder`, `graphify-nudge`, `archive-recall` |
| Asset | `assets/dpiRepair/resources/Repair-WinFormsDpiAnchor.ps1` | Deterministic scanner/fixer used by `dpi-anchor-fix` (detects DPI/AnchorLayoutV2, applies the config, `.bak` backup) |

## How it works

The plugin ships only skills, hooks, and assets that are **reusable across projects**. The
*Senior .NET Architect* persona, the agentic workflow, and the **C#/HMI rules** no longer
live in the plugin: they are project-specific and belong in the project itself —
the old *project brain* becomes the solution's `CLAUDE.md`, and the rule files
are copied/adapted into `.claude/rules/` (architecture, async-threading,
business-logic, csharp-idioms, data-communication, ui-controls, tests, etc.).
The skills that depend on the rules (`tdd`, `csharp-doc-comments`) read them from
the active project's `.claude/rules/*`, not from `${CLAUDE_PLUGIN_ROOT}`.

The three hooks replicate the behaviour of the original workspace:
- **archive-recall** (SessionStart) — recalls the recent change history from `.claude/claude-archive/`.
- **graphify-nudge** (PreToolUse on Bash/Grep/Glob) — if `graphify-out/` exists, suggests `graphify query` instead of grep.
- **build-reminder** (PostToolUse on Edit/Write) — reminds you to run `dotnet build` after editing `.cs` files.

> The hooks require **Python 3** on the PATH as `python`. They read `CLAUDE_PROJECT_DIR`,
> so they operate on the root of the project where the plugin is active.

## What is NOT included (on purpose)

The third-party tools of the original workspace (caveman, OpenSpec, graphify,
claude-mem, karpathy-guidelines) are installed separately — see the README of the
`Sistec.Claude.DeveloperHMI` repository. This plugin contains only what is
specific to Sistec.HMI development.

## Quick test

```bash
claude --plugin-dir ./plugins/hmi-developer
```

Then, in the session:

```shell
/hmi-developer:tdd
document this
```
