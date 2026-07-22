# Project documentation — README / architecture / solution docs (.NET)

On-demand module: load only when asked for project-level documentation, not for code comments.

Contents: 1. Before writing · 2. README · 3. Architecture doc · 4. Post-change triage · 5. Hard rules

## 1. Before writing anything

1. **Match the existing convention first.** Inventory what exists: root `*.md`, `docs/`, `Documentation/` folders, wiki links, doc style (voice, heading depth, badge use). Extend the established pattern; never impose a default over a working convention.
2. **Resolve canonical files.** `ls -la` root markdown files first — `README.md`/`CLAUDE.md`/`AGENTS.md` are often symlinked; edit the canonical target, not the alias.
3. **Smallest edit that fixes the gap.** Patch stale sections in place, preserving structure and voice; never rewrite correct content for style.

## 2. README (solution or project)

Target 50–100 lines; 200 is the ceiling. Structure for a .NET solution:

1. One-paragraph purpose (what the service/library does, for whom).
2. Solution layout — table: project | target framework | role | depends on.
3. Build & run — exact commands (`dotnet build SnifferService.slnx`, service install line); include only commands verified to exist.
4. Configuration — actual keys/files (e.g. `Config/Device.ini` sections), with real names from source.
5. Tests — how to run, which project is unit vs integration.

Anti-patterns: marketing prose ("blazing-fast"), line-count/badge padding, TODO placeholders shipped as sections, documenting commands or config keys that don't exist in the repo.

## 3. Architecture doc

Target 100–300 lines. Contents that earn their place:

- Project dependency direction (which project may reference which — one diagram beats prose).
- Runtime topology: hosts, workers, external endpoints (PLC/OPC UA servers, DBs).
- Key patterns actually used (e.g. `Device : TagProviderBase<T>` subscription flow, `AsyncPayload<T>` result piping) with one `<see>`-style pointer to the defining file each — not re-explained.
- Decision records for non-obvious choices (why INI not JSON, why per-device loggers), dated, append-only.

Diagrams as text (Mermaid): diffable, reviewable in a PR. One diagram per concern; no decorative diagrams.

## 4. Post-change triage — does this change need docs?

| Change | Docs action |
|---|---|
| New/renamed public API, breaking change, new config key | CRITICAL — update before finishing the task |
| New project, new external dependency, behavior change | Important — update in the same PR |
| Internal refactor, test-only change, comment fixes | Skip |

## 5. Hard rules

- Every command, path, key, flag, and code sample must exist in the repo and be runnable as written.
- Coverage gaps are reported, not filled with plausible text ("Configuration section pending — see `Configuration/DeviceConfig.cs`").
- Generated docs never overwrite hand-written sections that are still accurate.
