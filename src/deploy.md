---
description: Deploy a built Sistec Release output into production — copy the binaries into a named folder on one or more target machines, optionally creating a Desktop shortcut to the cell's main .exe. Binaries come from a Release folder (`--release`) or a zip (`--zip`; default = the `/versionize` output when chained via `versionize --deploy`). With `--version`/`-v <ver>`, the latest matching build of the exe ("last version") completes incomplete `--release` roots and `--name` wildcards (`HMI v*` → `HMI v3.27`, `…\Release` → `…\Release\HMI v3.27`). On any multi-`--dest` deploy the deployed version indicator is coordinated to the greatest across all sites (so the machines never show different versions — `HMI v3.27.2` + `HMI v3.27.1` → all `HMI v3.27.2`), independent of `--version`. Non-destructive & versioned side-by-side: a re-deploy of an existing name auto-increments a trailing index (`HMI v3.27` → `HMI v3.27.1` → `…2`); bare `/deploy` (no flags) re-deploys the last call (and so increments). With `--force`/`-f <version>`, the deployed folder's version is pinned to exactly `<version>` — bypassing the auto-increment collision logic (`-v 3.27 -f 3.27.2` deploys `HMI v3.27.2` even when `.1`/`.3` were the computed candidates) — and the cross-site coordination then pins every dest to that same `<version>`. After a successful deploy the run's release zip is renamed to carry the full deployed version index (`5309_FAEL v3.27.zip` → `5309_FAEL v3.27.5.zip` when deployed as `HMI v3.27.5`), and `--archive`/`-a <dir>` copies that renamed zip into a directory. The production-share write is gated by an explicit confirmation. Pairs with `/versionize`. Usage: /deploy --dest|-d "<path>" ["<path2>"…] --name|-n "<folder>" (--release|-r "<relPath>" ["<relPath2>"…] | --zip|-z "<archive>") [--version|-v "<ver>"] [--force|-f "<version>"] [--link|-l] [--archive|-a "<dir>"]  |  /deploy   (bare = re-deploy last, incrementing the index)
---

The user invoked **`/deploy`** to **push a built artifact into production**: copy a Release binaries
folder onto each target machine under a named folder, and optionally drop a Desktop shortcut to its
main executable. It **pairs with `/versionize`** — `versionize --deploy …` runs this as a final leg,
feeding its freshly-built zip as the default source. This is **not read-only**: it writes to a
production share, so the copy (and any shortcut) is **gated by an explicit confirmation** (Step 5).

1. **Parse the arguments** (flags order-independent; strip surrounding quotes from every value):
   - **`--name` / `-n` `"<folder>"`** *(required)* — the folder created under each `--dest` that will
     hold the binaries, **and** the base name of the `.lnk` when `--link` is set (e.g. `HMI v3.27`).
   - **`--dest` / `-d` `"<path>" ["<path2>"…]`** *(required)* — one or more destination roots the
     `<name>` folder is created under (collect every token up to the next flag; typically a UNC share,
     e.g. `\\192.168.10.10\Condivisa\Sistec`). One target machine per path.
   - **Binaries source — exactly one of:**
     - **`--release` / `-r` `"<relPath>" ["<relPath2>"…]`** — one or more **folders** already
       containing the built binaries (a Release output folder). *(Named `--release`, not `--source`/
       `-s`: `-s` is the workspace `--scope` convention.)* When the count matches `--dest`, sources
       map **positionally to dests** (cell-1 folder → machine-1, …); a single source fans out to all
       dests.
     - **`--zip` / `-z` `"<archive>"`** — a zip whose `Release/<cell>/<name>/` subtree holds the
       binaries; extract that subtree to a temp staging folder and use it as the source. **If `--zip`
       is omitted AND `/deploy` was invoked by `/versionize`** (Step 0 below), default the archive to
       versionize's just-built output zip (`<repos>\<root-leaf> v<ver>.zip`).
     - If **both** are given, `--release` wins (note it). If **neither** resolves, print usage + stop.
   - **`--version` / `-v` `"<ver>"`** *(optional — coordination mode)* — a single version (e.g. `3.27`,
     the app **major.minor**) that **completes the incomplete `--release`/`--name` parameters** and keeps
     every site on the **same** version (Step 1c). When present, `--name` may carry a `*` placeholder
     (`HMI v*`) and each `--release` may be a Release **root** (no versioned subfolder) — `--version`
     fills both from the **last (highest) built version of the exe**. Omitted ⇒ `--name`/`--release` are
     used verbatim (the pre-existing behavior).
   - **`--force` / `-f` `"<version>"`** *(optional — forced version index)* — pin the **deployed folder
     name** to exactly `<version>` (a complete dotted version, e.g. `3.27.2`), **overriding** Step 3's
     collision auto-increment and coordination (Step 3, forced branch). It sets only the deployed
     folder/`.lnk` version, **not** the binaries source: `--version`/`-v` still completes the
     `--release` root + resolves the built exe (`-v 3.27 -f 3.27.2` = build the last `3.27` exe, deploy
     it as `HMI v3.27.2`). If `<version>` is a bare index vs. a full `major.minor.idx`, treat it as the
     full version to substitute for the name's version token (Step 3). Omitted ⇒ auto-increment applies.
   - **`--link` / `-l`** *(optional flag)* — also create a Desktop shortcut named `<name>.lnk` →
     the deployed folder's **main `.exe`** (Step 4).
   - **`--archive` / `-a` `"<dir>"`** *(optional)* — after a successful deploy, copy the run's release
     zip (renamed per **Step 6a** to the deployed version) into `<dir>` (created if absent; a same-named
     archive is overwritten). Skipped — with a note — when the run has no associated zip (a `--release`
     deploy not chained from `/versionize`, so there is nothing to archive). Recorded with the other
     flags (below) so a bare-`/deploy` replay archives too.
   - **`-h` / `--help`** anywhere → P11 prints these parameters and does not execute.
   - **No flags at all → re-deploy the last call (Step 0b).** Don't error on missing required flags;
     replay the recorded last invocation instead.
   - Missing a required flag on a *flagged* call (`--name`, `--dest`, or a binaries source) → print the
     Usage synopsis and **stop**.
   - **Record the invocation** (every run that carries flags — not the no-flag replay, not chained legs
     that already came from a recorded versionize line): once parsed/validated, write the resolved
     flag set as one re-runnable line to `commands\deploy\last-args.txt` (overwrite) **before** Step 4,
     so a later bare `/deploy` replays it. The auto-increment (Step 3) then bumps the version on replay
     — unless `--force`/`-f` was recorded, which is sticky (a replay re-deploys the same forced name, no
     bump/overwrite).

   **Step 0 — chained invocation.** When run as a `/versionize --deploy` leg, versionize passes the
   deploy flags through and supplies its output zip; treat a `--zip`-less call as "use that zip".

   **Step 0b — bare `/deploy` (re-deploy last).** When invoked with **no flags**, read
   `commands\deploy\last-args.txt`; if missing/empty, say so and stop (suggest a full call). Otherwise
   replay that invocation verbatim — same `--dest`/source/`--name`/`--link`. Because the previous
   `<name>` now already exists at the dest, Step 3's **auto-increment** lands it on the next index
   (`HMI v3.27` → `HMI v3.27.1` → `…2`), giving a fresh side-by-side re-deployment. (Same effect as a
   `versionize --deploy` re-run with an unchanged `--name`.)

   **Step 1c — `--version` completion** *(only when `--version`/`-v` is set; skip entirely otherwise)*.
   Complete the incomplete `--release`/`--name` parameters from the **last (highest) built version of the
   exe** at version `<ver>`. *(This is only parameter-completion — the cross-site version coordination
   below in Step 3 is separate and applies to every multi-site deploy, with or without `-v`.)*
   - **Per-`--release` resolution ("last version of the exe").** A `--release` value that names a Release
     **root** (no cell `.exe` directly inside) is *incomplete*: enumerate its build subfolders matching
     the `--name` pattern at version `<ver>` — `<name with * → ver>` plus any auto-index suffix
     (`HMI v3.27`, `HMI v3.27.1`, …) — and pick the **last/highest** (the newest build present; confirm
     via the cell exe's FileVersion when ambiguous). The completed source = `<root>\<matched-folder>`. A
     `--release` already pointing at a concrete versioned folder (exe inside) is used as-is. If nothing
     matches `<ver>` under a root, fall back to the literal `<root>\<name with * → ver>` and let Step 2
     validate it exists.
   - **Complete `--name`:** substitute `*` with `<ver>` (`HMI v*` → `HMI v<ver>`); a `--name` without `*`
     is used verbatim.
   - Hand the completed `--release` list + `--name` to Steps 2–6.

2. **Resolve the binaries source(s) → a concrete folder per `--dest`.**
   - `--release`: each path must be an existing folder containing at least one `.exe`; use as-is.
   - `--zip`: confirm the archive exists; locate the `Release/<cell>/<name>/` entry (or, when a single
     cell, the lone `Release/*/<name>/`); extract it to a scratch staging dir under the session
     scratchpad. One staged folder per cell.
   - Validate every resolved source folder is non-empty and holds the cell `.exe` (e.g.
     `Sistec.5309AB.exe` / `Sistec.5309C.exe`). If a source can't be resolved, say which and **stop**.

3. **Compute the deploy plan (per dest × source) — auto-increment the version index on collision.**
   For each `--dest`, resolve the **effective folder name** so a re-deploy never overwrites and lands
   side-by-side:
   - **Forced version (`--force`/`-f` set) — pin the name, skip auto-increment + coordination.** The
     effective name is the base `--name` with its **version token forced to `<version>`**: substitute a
     `*` placeholder with `<version>` (`HMI v*` → `HMI v3.27.2`), else replace the trailing dotted
     version of `--name` with `<version>` (`HMI v3.27` → `HMI v3.27.2`). Use this single forced name for
     **every** `--dest` (the coordination below is satisfied by construction — all sites share
     `<version>`). Because the forced name **may already exist**, this can overwrite that sibling
     folder — the auto-increment safety net is intentionally bypassed; flag the overwrite in the Step 4
     gate (`HMI v3.27.2 already exists → will be overwritten`) and still never touch *other* version
     folders. Then skip the auto-increment + greatest-candidate coordination bullets below.
   - Take the base name `B` = `--name` (e.g. `HMI v3.27`). Enumerate existing folders in `<dest>`
     matching `^<B>(\.<digits>)?$` (i.e. `B` itself = index 0, or `B.<N>`). **Escape `B` for the
     regex** — it contains dots (`v3.27`), so match `B` literally then an optional `.<N>` suffix; never
     strip `B`'s own `.27`.
   - **If none match** → effective name = `B` (first deployment).
   - **If some match** → effective name = `B.<max-index+1>` (`B` present → `B.1`; `B`+`B.1` → `B.2`; …).
     The `.<N>` is a **3rd/4th dotted index appended to the whole base** — `HMI v3.27` → `HMI v3.27.1`
     → `HMI v3.27.2`. Compute the candidate **per dest** first (each target machine tracks its own
     existing folders).
   - **Coordinate the version indicator across sites (mandatory for any multi-`--dest` deploy — the
     Notice; independent of `--version`).** When more than one `--dest` is targeted at once, the per-dest
     candidates above can differ (machine-10 already holds `HMI v3.27.1` → wants `.2`; machine-11 holds
     only `HMI v3.27` → wants `.1`). The two machines **must not** show different versions: take the
     **greatest** candidate effective name (compare by its dotted-numeric parts) and apply that single
     **coordinated** name to **every** dest (`HMI v3.27.2` + `HMI v3.27.1`/`HMI v3.27` → all
     `HMI v3.27.2`). Each dest still copies its own source; only the deployed folder name + `.lnk` base
     are unified. (A single-dest deploy has nothing to coordinate — its candidate is the effective name.)
   - Target folder = `<dest>\<effective-name>` (the coordinated name for multi-site). Never delete or
     overwrite a sibling version folder.
   - Size the copy (file count + MB) from the source.
   - If `--link`: resolve the **main exe** = the `.exe` matching the cell app (`Sistec.5309AB` /
     `Sistec.5309C`), **excluding** the bundled `Sistec.BS.exe`; tie-break by largest. The shortcut is
     named for the **effective** name: path = `\\<dest-host>\Users\User\Desktop\<effective-name>.lnk`
     (observed convention — target user `User`; if the dest host/user differs, say so). **TargetPath =
     the target-LOCAL exe path, NOT the UNC** (field-confirmed 2026-06-30 — see Notes): the `Condivisa`
     share is published from the target user's Desktop, so `\\<dest-host>\Condivisa\…` mirrors to
     `C:\Users\User\Desktop\Condivisa\…` on the target. TargetPath =
     `C:\Users\User\Desktop\Condivisa\Sistec\<effective-name>\<exe>`, WorkingDirectory = that local
     folder. (Set it as an explicit absolute string from the deploying host — COM stores the literal and
     does **not** rewrite it to the author host; verify the read-back equals the intended local path.)

4. **Present the plan and get explicit confirmation (GATE).** Show, per dest: source →
   `<dest>\<effective-name>` (file count/MB), the **resolved version index** (e.g. base `HMI v3.27`
   already present → deploying as `HMI v3.27.1`), and the shortcut to be created (path → exe target)
   when `--link`. **This writes to production — wait for the user's explicit OK before copying
   anything.** The auto-increment means a re-deploy is safe by default (new side-by-side folder); the
   confirmation is the gate, not a request to rename.

5. **Execute the deploy (after confirmation).** Per dest:
   - **Copy** the source tree into `<dest>\<effective-name>\` — a recursive, **incremental** mirror
     (skips unchanged files) run **in the background with an observable progress log**:
     `robocopy "<source>" "<dest>\<effective-name>" /E /NP /NDL /NJH /V /LOG:"<scratch>\deploy-<dest-host>.log"`
     (start it with `run_in_background`). **`/V` logs one line per file** (copied *and* skipped-as-same)
     so the log advances toward the source's total file count; `/NP` drops the per-byte spam, `/NDL` the
     dir lines. **robocopy is incremental by default** — it transfers only changed/new files (same size +
     write-time ⇒ skipped), so a force-overwrite re-deploy only sends what differs. **No `/MIR` or
     `/PURGE`** — add/update only, never prune dest-only files. `Copy-Item -Recurse` is the fallback (not
     incremental — prefer robocopy). At the end, read the robocopy **summary + exit code** from the log
     (0–7 = success, ≥8 = failure). Create the folder if absent; never delete sibling version folders.
   - **Progress + on-demand feedback (make a long copy observable).** Know the source total up front —
     **file count `N` + total bytes** (from Step 2/3). While the background copy runs, compute
     **completion % = min(100, `processed` / `N` × 100)**, where `processed` = the count of file lines in
     the robocopy `/V` log. **Use the file-processed count, not dest byte-size** — on a force-overwrite
     the dest is already ~full, so its size barely grows and would misreport ~100% from the start; the
     `/V` log line count advances monotonically regardless.
     - **Periodic (~every 10%):** poll the log tally (a light loop / the Monitor tool) and **emit a
       one-line update each time completion crosses the next ~10% boundary** (10 → 20 → … → 100), e.g.
       `Deploy .10 HMI v3.27.2: ~40% (245/611 files, ~38/95 MB)`. **Speak only on a threshold crossing**,
       never per sample; one progress track per `--dest`.
     - **On demand:** if the user asks mid-copy ("how far?"), read the current tally and answer the
       **instantaneous %** — `~25% — 150/611 files, ~24/95 MB` (+ a rough ETA from the byte rate). This
       is a read of the live log, not a new copy.
     *(Same pattern fits any long op with a countable unit — e.g. `/versionize --zip` packaging by
     entries added; wire it there if packaging time becomes a concern.)*
   - **`--link`:** create the `.lnk` via `WScript.Shell` `CreateShortcut`, setting `TargetPath` to the
     **target-local** exe path (Step 3) + `WorkingDirectory` to the local folder, and saving to the
     resolved remote Desktop path. **Verify the read-back** (`CreateShortcut(path).TargetPath`) **equals
     the intended local path** — confirms COM stored the literal and didn't rewrite it to the author host.
     If the dest's `\\<host>\Users\User\Desktop` is **access-denied** (observed on some targets), the copy
     still succeeds — report the `.lnk` as skipped and tell the user to create it on that machine.
   - If a dest is unreachable or a copy fails, report it and continue with the remaining dests (don't
     abort the whole run); summarize failures at the end.

6. **Rename the release zip to the deployed version, then archive it (`--archive`).** Runs after a
   successful deploy (skip if **every** dest failed). Operates on **the run's release zip** = the
   `--zip` source if one was given, else — when chained from `/versionize` (Step 0) — that run's output
   zip `<repos>\<root-leaf> v<major.minor>.zip`. If neither exists (a plain `--release` deploy with no
   associated zip), skip both sub-steps (and note it if `--archive` was requested — there is nothing to
   rename/archive).
   - **a. Rename to the deployed version — carry the full index.** Rename the zip so its version token
     matches the **coordinated effective deployed folder version** (Step 3), carrying the full dotted
     index when the deploy landed on one: `<root-leaf> v<major.minor>.zip` →
     `<root-leaf> v<full-version>.zip` — e.g. deployed as `HMI v3.27.5` → `5309_FAEL v3.27.zip`
     becomes `5309_FAEL v3.27.5.zip` (all three parts `3.27.5`); `--force 3.27.2` → `… v3.27.2.zip`.
     If the effective name carries **no index beyond major.minor** (`HMI v3.27`), leave the zip name
     unchanged (nothing to carry). The coordinated version is a single value across every `--dest`
     (Step 3), so one zip name matches all sites. Rename in place under `<repos>` (`Rename-Item`).
   - **b. Archive (`--archive` / `-a <dir>`).** When `--archive`/`-a` is set, **copy** the (renamed) zip
     into `<dir>` — create the directory if missing; overwrite a same-named archive there. The working
     zip stays in `<repos>`; this is a copy, not a move. Report the archived path + size. Without
     `--archive`, skip (the rename in 6a still happened).

7. **Report.** Per dest: target folder + file count/MB copied (+ robocopy result), the shortcut created
   (path → target) or skipped, and any failures. Note the source provenance (which `--release` folder
   or `--zip`), when chained that the source was versionize's output, **the renamed zip name (Step 6a)
   and — when `--archive` — the archived copy's path (Step 6b)**. Clean up any zip-staging scratch.

Notes / constraints:
- **Production write, gated.** `/deploy` copies into a live production share and may create a Desktop
  shortcut — irreversible/outward-facing, so Step 4's confirmation is mandatory (this is *not* a
  read-only command). It never deletes existing version folders (non-destructive, side-by-side).
- **Incremental copy — unchanged files are skipped.** The copy transfers only changed/new files
  (robocopy's default size+write-time compare; no `/MIR`/`/PURGE`), so a force-overwrite re-deploy into
  an existing folder is cheap and only updates what differs — it never prunes dest-only files.
- **Zip renamed to the deployed version, then optionally archived (Step 6).** After a successful deploy
  the run's release zip (the `--zip` source, or the chained `/versionize` output `<repos>\<root-leaf>
  v<major.minor>.zip`) is renamed **in place** to carry the full coordinated deployed version index
  (`5309_FAEL v3.27.zip` → `5309_FAEL v3.27.5.zip`); it is left unchanged when the deploy landed on a
  bare `major.minor` name. `--archive`/`-a <dir>` then **copies** that renamed zip into `<dir>` (the
  working zip stays in `<repos>`). A plain `--release` deploy with no associated zip skips both (noted).
- **Progress + on-demand feedback.** The copy runs in the background with a robocopy `/V` log; progress
  is `processed-file-lines / source-file-count` (not dest byte-size — a force-overwrite starts near-full).
  Report a one-line update on each ~10% crossing, and answer the instantaneous % on demand. Requires the
  `/V /LOG` invocation (drop `/NFL`) + knowing the source file count up front.
- ✅ **Shortcut target = the target-LOCAL path (field-confirmed 2026-06-30).** A `.lnk` pointing at the
  **UNC** exe (`\\<host>\Condivisa\Sistec\…\app.exe`) is broken for this site in two ways: (1) launching
  from a UNC puts the file in the network zone → Windows blocks it with *"Impossibile verificare il
  creatore del file. Eseguire il file?"*; (2) it isn't how the site's working links are built. The
  `Condivisa` share is **published from the target user's Desktop**, so `\\<host>\Condivisa\Sistec\<name>`
  is the same folder as the target-local `C:\Users\User\Desktop\Condivisa\Sistec\<name>` (verified: an
  existing working link resolved to exactly that local path). **So set TargetPath + WorkingDirectory to
  the local mirror** `C:\Users\User\Desktop\Condivisa\Sistec\<effective-name>\<exe>`. Set it as an
  explicit absolute string from the deploying host — COM stores the literal (it does **not** rewrite it to
  the author host when an absolute target is assigned) and the read-back confirms it. (The earlier
  author-host-path symptom was avoided here by assigning the absolute string, not a relative/resolved one.)
  If a different site maps the share elsewhere, derive the local root from one of its existing working
  links and adjust.
- **Multi-cell:** run once per cell (AB → its machine, C → its machine), or pass matching
  `--release`/`--dest` lists; sources map positionally to dests, a single source fans out.
- `robocopy` / `WScript.Shell` / share access may prompt the first time — handle per **P6**; don't
  pre-add allow-rules. Writing `.claude\commands\*.md` is agent-config self-modification.
- Built by `/skillify` + this distillation; spec/trace under `commands\deploy\`. Chained from
  `/versionize --deploy`.
