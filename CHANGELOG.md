# Changelog

Notable changes to the marketplace plugins. Format inspired by
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are those of the individual plugins.

## 2026-10-02 — Marketplace translated to English

**blender-ply 0.1.0 → 0.2.0 · technical-writer 0.2.2 → 0.3.0 · hmi-developer 0.3.0 → 0.3.1 ·
git-release 0.3.0 → 0.3.1 · log-forensics 0.2.0 → 0.2.1 · device-spy 0.1.1 → 0.1.2 ·
hello-sistec 0.1.0 → 0.1.1** · branch `chore/translate-to-english`

### Changed

- READMEs, manifests (`marketplace.json`, `plugin.json`), SKILL.md files, agents, templates, code
  comments and script/hook messages translated from Italian to English. This changelog too.
- The quoted Italian trigger phrases stay in the skill descriptions, so Italian requests still
  trigger the skills; technical-writer and maintain-manual gained a few.
- Italian that is output or data stays Italian: the manuals produced by technical-writer and
  maintain-manual (and the Italian sample `assets/exampleManual.md`), the archive note headings of hmi-developer, the SQL sample values of
  `translate`, PLC/HMI symbol names and network paths.
- **technical-writer**: technical-writer and maintain-manual now state explicitly that the manual is
  written in Italian; spec-document still writes in the language of the request.

### Renamed (breaking)

- **blender-ply** skills and scripts:
  - `/blender-ply:visualizzaply` → `/blender-ply:view-ply` (`view_ply.py`)
  - `/blender-ply:centrablender` → `/blender-ply:center-blender` (`center_blender.py`)
  - `/blender-ply:centraply` → `/blender-ply:center-ply` (`center_ply.py`; undo step
    "CentraPLY" → "CenterPLY")
  - `/blender-ply:fotografaply` → `/blender-ply:snapshot-ply` (`snapshot_ply.py`)
- **technical-writer**: `assets/struttura-manuale.template.md` → `assets/manual-structure.template.md`;
  the project outline is now `docs/manual-structure.md`. A legacy `docs/struttura-manuale.md` is
  still read.

## 2026-10-02 — New blender-ply plugin

**blender-ply 0.1.0** · branch `feat/blender-ply`

### Added

Plugin for working in Blender, through the MCP bridge, on PLY models exported from CAD (in mm,
per-vertex colours, no materials). The skills come from real usage sessions.

- `/blender-ply:visualizzaply`: after the import, makes the per-vertex colours visible, computes the
  clip from the model diagonal, sets a centred 3/4 view and enables *Zoom to Mouse Position* +
  *Auto Depth*.
- `/blender-ply:centrablender`: centres the model on its on-screen silhouette without changing the
  inclination; the zoom moves out only if the model does not fit.
- `/blender-ply:centraply`: brings the selected vertex (or the midpoint) to (0,0,0), making the
  object origin, 3D cursor and world origin coincide. It moves the mesh, so it also holds in the
  exported PLY.
- `/blender-ply:fotografaply`: saves a PNG on a white background without overlays through a
  viewport render (view transform `Standard`, because with AgX white comes out grey), then restores
  the view.
- `/blender-ply:ply-colors`: restores per-vertex colours (Solid → `VERTEX` and a material for
  Material Preview); `detect_ply_colors.py` is the read-only version.
- `PostToolUse` hook `ply-colors-nudge.py`: after a PLY import or on the first Blender call of the
  session it queries Blender read-only and warns only if a model is really shown grey.
- Optional rule `rules/blender-ply-colors.md`, to be copied by hand into `~/.claude/rules/`.

### Compared with the original skills

- Portable paths: the scripts are loaded from `${CLAUDE_SKILL_DIR}` with an `exec` wrapper, instead
  of from a user path hard-coded in the code. `ply-colors` now uses the wrapper too and no longer
  sends the whole script into the conversation.
- The viewport math (projection, centring, world-space vertices) lives in
  `lib/view_projection.py`, instead of being duplicated in three scripts. Equivalence with the old
  centring loop was verified on 300 random cases.
- `blender-ply-colors` renamed to `ply-colors`, to avoid `/blender-ply:blender-ply-colors`.
- SKILL.md files and script messages in English; the Italian trigger phrases stay in the descriptions.

### Fixed

- Hook: the message reported the `color_type` of the first view instead of the wrong one.
- `centraply`: also detects rotations in quaternions or axis-angle (`matrix_basis` instead of
  `rotation_euler`).

## 2026-09-24 — Token-usage reduction for gitize, versionize, track-timing

**git-release 0.2.0 → 0.3.0 · log-forensics 0.1.1 → 0.2.0** · branch `perf/skill-token-reduction`

### Motivation

Usage statistics 2026-06-20 → 2026-09-17 (attributed list-price cost, not actual spend):

| Skill | Invocations | Attributed cost | Cost per invocation |
| --- | ---: | ---: | ---: |
| trackTiming | 115 | $544.65 | ~$4.74 |
| versionize | 78 | $194.63 | ~$2.50 |
| gitize | 222 | $327.65 | ~$1.48 |

The skill text weighed little (2–4.5k tokens). The cost came from the work the model did: dozens of
git/DLL/grep commands run one at a time, raw outputs read in full, tables regenerated by hand and the
session context paid again on every turn.

### Changed

**gitize**
- Frontmatter `context: fork` + `model: haiku`: runs in an isolated subagent on a cheap model.
- New `scripts/collect-changes.ps1`: a single call resolves the target, discovers the repos and
  returns status + stat + zero-context hunks. Diff budget: 300 lines per file, 600 per repo, 1500 in
  total. Beyond the budget the summary is file-level only, always declared. Untracked bin/obj noise
  is ignored and `.slnx` workspaces are detected.
- SKILL.md from 8.5 to 3.7 KB.

**versionize**
- Frontmatter `model: sonnet`, without fork: the pre-flight gate uses `AskUserQuestion`, which is not
  available in forks.
- New `scripts/collect-release-facts.ps1`: a single compact JSON with git facts, pre-flight
  (dirty / operations in progress / stale build / unpushed), most recent build per executable
  project, DLL identities, frameworks, central packages and changelog with `-Since` for `-upd`.
- `-new` starts from `FeatureCatalog.md` and reads only the git delta (`--since=<snapshot>`); `-upd`
  never reads the source.
- The explanations are in `references/details.md`. SKILL.md from 17.6 to 6.9 KB.
- Fix: `git log <date>..HEAD` (invalid revision, already present in the previous version) replaced
  by `--since=<date>`.

**track-timing**
- Frontmatter `context: fork` + `model: sonnet`.
- New `scripts/scan_timing.py` (Python, stdlib only):
  - parses all the logs (about 9 s for 1.4 M lines);
  - rebuilds the per-job chains and reports anomalies, cycles, races and device health;
  - correlates the sources within ±5 s on a single timeline;
  - writes the report tables directly and keeps the analyst's text between the `BEGIN`/`END`
    markers;
  - updates `parts-issued.md`;
  - prints a digest with only the anomalies that are **new** since the last run (high-water mark per
    file; `--full` to review them all).
- New `scripts/sync_logs.py` for `--upd`: skips the backlog, appends only the new tail, replaces
  rotated files.
- Artefact catalogue and baseline checklist saved in `.trackTiming/`.
- The event-chain vocabulary is in `references/event-chains.md`. SKILL.md from 14.7 to 6.7 KB.

**Other**
- Updated the step references in `package-release` and `git-split-commits`.
- Updated the READMEs.

### Benchmark

Six runs: each skill once with the new version and once with the original version (pre-change
snapshot), on identical fixtures. Same model for both, so the comparison measures only the workflow.
The frontmatter `model`/`context: fork` settings do not come into play.

| Skill | Fixture | Tokens new / original | Duration | Tool calls | Checks new / original |
| --- | --- | --- | --- | --- | --- |
| gitize | 3 repos: small change, 700-line file + 1 line, untracked bin only | 46,560 / 50,807 (**−8%**) | 29 s / 55 s | 4 / 8 | 4/4 / 3/4 |
| versionize | `-new`, dirty tree, build 1 commit behind | 56,796 / 64,625 (**−12%**) | 96 s / 128 s | 11 / 15 | 4/4 / 4/4 |
| track-timing | 2 synthetic logs (8 jobs, FAIL/RETRY, handshake FAIL, inconsistency, race, unknown artefact) | 64,140 / 84,676 (**−24%**) | 116 s / 183 s | 13 / 10 | 6/6 / 6/6 |
| **Total** | | 167,496 / 200,108 (**−16%**) | 241 s / 366 s (**−34%**) | 28 / 33 | 14/14 / 13/14 |

Automatic checks:
- **gitize**: Conventional-Commits subject ≤ 72 characters; Retry mentioned; C3 change (3 → 33)
  described; `Repos:` footer without Demo.App. The original version lost the C3 change, because it
  discarded the whole repo beyond 600 lines.
- **versionize**: 4 sections in the right order; DLL versions 3.25.4.0 / 2.10.1.0; drift `5e66b02`
  reported; dirty tree recorded.
- **track-timing**: report name `SPV_5309AB+C_<date>`; handshake FAIL of job 1005; inconsistency
  batch 1007/1006; race 6/24; 24 rows in `parts-issued.md`; artefact `notes.bin` reported.

track-timing parser on a 1,392,000-line log: 2 min 33 s in the first draft (O(n²) correlations),
**8.7 s** after using `bisect` and the literal prefilter.

### How to read the numbers

- Every run includes a fixed cost of about 40k tokens (the subagent's system prompt and tools). Net
  of this, the reduction in the skill-specific work is much larger than the percentages in the
  table.
- The fixtures are small. With the original versions the cost grows with the size of diffs and
  logs; with the new ones it stays almost constant, because the model reads only compact digests.
- In real use two effects add up that the benchmark does not measure:
  - the cheaper model (haiku for gitize, sonnet for track-timing and versionize);
  - the fork, which does not carry the conversation along.
- For track-timing, the runs after the first show only the new anomalies.

### Validation of `scan_timing.py` on production logs

Real logs copied from `\\192.168.10.10` (AB) and `\\192.168.10.11` (C): `SPV_5309AB/5309C` of
2026-09-22 (a day with problems: 50k "Reconnect") and of 2026-09-23 (a normal day), build
v3.32.9761. 161,565 lines in total.

**Patterns fixed compared with the first draft** (written on the synthetic logs):
- Job IDs: `Job(Job[3108], …)` and `Job_3108`.
- The `… SendPressConfigurationAsync progress: <stage>` lines were counted as new sends.
- Startup banner: `: Sistec.5309AB v3.32…`.
- State transitions `A -----------> B` and real states: Cancelled, Resumed, Paused,
  ReadyToRestart, NextRunning, plus numeric values.
- Handshake timeouts (`HandShake.* waiting … Timeout`).
- Real messages of OpcUaClient SistecPLC/BSPLC, UAClient, Modbus connector, Kuka/TcpClient.
- Send outcomes (SUCCESS/FAIL/RETRY) attributed to the job that opened the send.
- Mode/BendIndex change reported only right after a RETRY.
- **Cycle Δ**: on the real line the part reaches zone 1 minutes after `OnNewPart`. The first draft
  paired within ±30 s and matched 4 parts out of 47; it now pairs by order within the batch and
  matches 46/47 and 60/60.
- Flood detection: on 22/09, 42,286 KeepAlive lines, 44% of the log.

**Comparison with an independent `grep`** (identical counts on all 4 files):

| Event | AB 22/09 | AB 23/09 | C 22/09 | C 23/09 |
| --- | ---: | ---: | ---: | ---: |
| Handshake FAIL | 1 | 3 | 0 | 0 |
| HandShake timeout | 2 | 8 | 0 | 0 |
| SendPressConfigurationAsync FAIL / RETRY | 0 / 0 | 2 / 1 | — | — |
| Parts (OnNewPart) | 60 | 47 | 0 | 0 |
| Application starts | 4 | 10 | 2 | 5 |
| Kuka events | 1,670 | 255 | 18 | 64 |
| UAClient events | 42,365 | 65 | 2 | 6 |

SistecPLC: the parser also counts `SetValueWriteToBus … FAIL` (48 = 39 + 9 on 22/09). The per-job
chains were rechecked by hand line by line. Performance: 0.65 s for 55k lines. A second run on the
same file gives 0 new anomalies and 0 duplicate parts. `sync_logs.py` on the real snapshot of 24/09
appends only the tail.

**Comparison with the report of the old `/trackTiming`** (`SPV_5309AB_20260609.md`, build v3.25),
re-running the parser on the same log (13,948 lines) and on the same `plc_reports_20260608/09.json`
taken from the NAS (`5309_FAEL-Coordination`):

| Finding of the old report | New parser |
| --- | --- |
| Job 1698: LoadProgramFail → FAIL → RETRY with Mode 8→1 → Handshake FAIL (TaskCanceledException on `Z02_PressbrakeProgramLoaded`) | ✅ same chain, same lines (L5008–L5198) |
| `SendPlcPressProgramInconsistency` idBatch 1708 / roller 1704 (L12771) | ✅ |
| Double FollowRobot + LoadProgram send within 200 ms (L12785) | ✅ 0.200 s |
| Jobs 1701 and 1704 clean | ✅ CONSISTENT |
| 23 cycles in zone 1, no race | ✅ 0/23 |
| SistecPLC burst 08:25:48 → 08:26:55, heartbeat tags only | ✅ 34 events, `*_LIVE`/`LiveBit_HMI` |
| `plc_reports`: 1,982 rows (148 ALM / 190 WRN / 36 CMD / 1,608 STA) and 6,107 rows | ✅ identical counts |

**Fixes that came out of the comparison:**
- `plc_reports`: `DataTime` contains only the time; the date is taken from `created_at`. Before, 0
  rows were read.
- `PunchingCompleted` is the valid end for the punching cell, because `Completed` arrives only when
  the order is closed. The 5 false "MISSING-END" of 09/06 are gone, and job 3102 of 22/09, previously
  reported, is now CONSISTENT too.
- `LoadProgramFail` is counted once per send, not 6 times (the popup lines repeat it).
- Always-active ALM/WRN codes (more than 30 occurrences, for example `Stations_GeneralWrn_Main_38`)
  are excluded from the correlation as background noise.

Known and accepted differences:
- Modbus: the old report mentions 178 "Reconnect", but no such line exists in the log, only
  `ModbusClient.WriteMultipleRegisters leave`, which the report itself judged routine.
- The parser does not track the back-gauge popup (confirmed or skipped) nor the formatting of
  `OnPressBrakeProgramNameChanged`. These are path details that the old report described as benign.

Not validated: the old reports of 12 and 13/07 (their logs are not on the NAS) and the baseline
checklist (`SystemCoordination.md` found and copied; the checklist is extracted by the model, not by
the script).

### Known limitations

- With `context: fork` the skill does not see the conversation: for gitize and track-timing the
  target must be passed as an argument. If it is missing, gitize uses the current folder and
  track-timing the most recent log of the active project. track-timing cannot ask questions, so it
  puts them in the final report.
- The `scan_timing.py` patterns are validated on build v3.32.9761 (see above). If a future build
  renames a message, the `P` list at the top of the script must be updated, together with the
  `PREFILTER` keywords.
- Attributing events without an ID (press sends, handshakes) to jobs follows the "current job",
  i.e. the last one that went into Running. With two jobs overlapping at a job change, some events
  may end up on the adjacent job.
