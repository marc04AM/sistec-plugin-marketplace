---
description: Turn an HMI's MissingTranslations.csv into the SQL that upserts the missing terms into the canonical language_spv table. Resolves the DB from DB.ini + DevOverride, infers each key's Italian/English from its code call-site, keeps StringName EXACTLY as the lookup key (incl. a leading '#'), writes an idempotent ON-DUPLICATE-KEY upsert, and dry-run-validates it in a rolled-back transaction. Default = generate + validate only (you run it); --apply executes it (gated). --rescan folds an updated/rotated CSV's emergent keys in and drops superseded ones (P14). Usage: /translate [-fn "<MissingTranslations.csv>"] [--scope|-s "<.sln, project, or folder>"] [--db <DB_n|name>] [--out "<path>"] [--rescan] [--apply]
---

The user invoked `/translate` to convert an HMI's logged **missing translations** into ready-to-run
SQL against the **canonical translations table** (`language_spv`). Distilled (via `/skilliDo`) from the
2026-06-28 5309_FAEL run. Multi-repo aware (reuses the [[gitize-command]] repo-set cache to locate the
source + Config). Links [[fael-solution]] [[git-repos-sistec-5309abc]]. **Default mode is read-only on
the DB** — it generates the `.sql` + a rolled-back validation and hands off (you run it); **`--apply`**
is the only mode that writes, and it is gated. Any file written inside a repo is left **unstaged** (P15).

1. **Parse arguments** (order-independent; `-h`/`--help` → P11 prints the Usage and stops):
   - `-fn "<path>"` → the `MissingTranslations.csv` (strip quotes). Optional → newest
     `**/bin/**/MissingTranslations.csv` under the scope (youngest by write-time).
   - `--scope` / `-s "<path>"` → the `.sln`, project file, or folder that holds **both** the source
     code (translation call-sites) **and** the `Config\` (DB.ini / DevOverride). Optional → the
     **active project's solution** (resolved from its ledger, like [[gitize-command]]).
   - `--db <DB_n|name>` → which `DB.ini` entry is canonical (default **`DB_0`**).
   - `--out "<path>"` → output SQL file (default `<csv-dir>\MissingTranslations.sql`).
   - `--rescan` → P14 incremental: the CSV was processed before; re-derive and **merge** into the
     existing `--out` (Step 8) instead of writing fresh.
   - `--apply` → after generating + validating, **execute** the SQL against the DB (Step 9, gated).
   A given-but-nonexistent `-fn`/`--scope` path → print Usage and **stop**.

2. **Resolve the canonical database (DB.ini + DevOverride).** Recall memory first (P0). Read
   `<scope>\…\Config\DB.ini`, take the `--db` entry (default `[DB_0]`: `Database`, `IP`, `UserName`,
   `Password`, `Driver`), then overlay `DevOverride.Debug.ini` — the debug build's `db_<n>_Database`,
   `db_<n>_IP`, `db_<n>_UserName`, `db_<n>_Password` **win** over DB.ini. The resolved tuple is the
   target. **Credentials are ephemeral (P9)** — use them only for the immediate query; never write them
   to the SQL, report, ledger, or memory; refer to them by role. For `Driver = MySql`, locate
   `mysql.exe`; run `SELECT VERSION();` — the **5.7 vs 8.0** answer picks the Step-7 upsert syntax.

3. **Confirm the lookup mechanism from code (the crux — verify, don't assume).** Check how the app
   resolves a term (`Sistec.Core` `TranslationManager` / `Translations`): it is an **exact dictionary
   hit — no `#` stripping**. Therefore:
   - **`StringName` MUST equal the raw key** passed in code: keys written with a leading `#`
     (`"#ProductionLog"`, `"#JobSplit*"`) are stored **with** the `#`; keys without one (`plc_PLC_0`)
     have none. This is the single most important correctness rule — get it wrong and the term never
     resolves at runtime.
   - The leading `#` in the CSV **DefaultText** column is only the runtime "untranslated" marker.
   - `SHOW CREATE TABLE language_spv` to confirm the columns (`StringName` PK, `Italian`, `English`,
     `Other`, `TimeStamp DEFAULT CURRENT_TIMESTAMP`).

4. **Parse the CSV → distinct keys.** Columns `Timestamp;Locale;Key;DefaultText;Module;Method`.
   Collapse to **one row per distinct `Key`** (a key logs once per locale); keep each key's
   `DefaultText`, `Module`, `Method` — they point at the call-site for Step 5.

5. **Infer Italian + English from the call-site (not the CSV alone).** For each key, grep the source
   at `Module`/`Method` (and the `GetOrDefault(key, default)` call) to read the **intended text** and
   its meaning, then produce a clean **Italian** and **English** value:
   - the `#`-stripped DefaultText is the author's fallback — usually right for one language; supply the
     natural translation for the other;
   - disambiguate from context (title vs body, column header, enum member, units);
   - **preserve `string.Format` placeholders** (`{0}`, `{1}`, …) verbatim in both languages;
   - **flag every value you had to guess** (no human-readable default in code) for the user to vet.

6. **Check the table — report existing vs new.** Query `language_spv` for the candidate `StringName`s
   (`WHERE StringName IN (…)`, `--default-character-set=utf8mb4`). Report which already exist (with
   their current IT/EN, so the user sees what an upsert would overwrite) vs which are new. Reporting
   only — the Step-7 upsert is safe either way.

7. **Generate the SQL file (`--out`).** One multi-row, **idempotent** statement:
   `INSERT INTO language_spv (StringName, Italian, English) VALUES (…), (…)` + the upsert tail chosen
   by the Step-2 version:
   - **MySQL ≤ 8.0.18 (e.g. 5.7):** `ON DUPLICATE KEY UPDATE Italian=VALUES(Italian), English=VALUES(English);`
     (the `VALUES()` function form — the `AS new` alias form is a parse error before 8.0.19).
   - **MySQL ≥ 8.0.19:** either works; default to the `VALUES()` form for portability.
   `StringName` = the exact key (incl. `#`); leave `TimeStamp`/`Other` to defaults; write **UTF-8**
   (accented IT text); group the tuples by area with a comment per group; lead with a header comment
   naming the source CSV + the resolved DB (name/host/driver — **never** the password) + the rules
   (exact-key, `#`-marker, idempotency).

8. **Validate — always; rolled back (no persistence).** Pipe `START TRANSACTION;` + the file +
   `SELECT ROW_COUNT(); … ; ROLLBACK;` through the client; confirm it parses, the affected count
   equals the tuple count, and accents round-trip. Nothing is committed.
   - **`--rescan` (P14, rotation-aware):** the CSV is append-only but **rotates** (a new run resets
     it). If it shrank/restarted (line count < last, or earlier timestamps), treat it as a fresh full
     scan. Diff the current distinct-key set against the existing `--out`: **add emergent** keys and
     **remove superseded** ones (a key whose producing call-site is gone, or an error key replaced —
     verify by grep). Merge into the existing file in place; note what was added/removed.

9. **Default: stop and hand off. `--apply`: execute (gated).** Default mode ends here — report the
   `.sql` path, the existing-vs-new split, and the flagged guesses, and give the run command
   (`mysql -h <ip> -u <user> -p <db> --default-character-set=utf8mb4 < <out>`). With **`--apply`**,
   present the exact statement + target DB and **ask for confirmation**; on approval run the file, then
   re-query the candidates to confirm the rows landed. A `--out` inside a git repo is left **unstaged**
   (P15).

10. **Report + persist.** Summarise: resolved DB, CSV (+ rotation state if `--rescan`), counts
    (distinct / new / existing / guessed), output path, applied?. Append the request/result to the
    active project's `*.log.md` ledger (P2); capture any durable finding (the exact-key rule, a
    recurring DB-override path) to memory (P0.4).

Notes: global command. **Default mode is read-only on the database** (a `.sql` + a rolled-back
validation) — no gate; **`--apply` writes to the DB and is gated** (Step 9). The DB password is
**ephemeral** (P9) — never written anywhere. **`StringName` fidelity (exact key, `#` kept)** is the
chief correctness rule (Step 3). The MySQL-version detection (Step 2) auto-selects the upsert syntax —
no flag. A `mysql.exe` invocation may prompt for permission the first time — handle per P6, don't
pre-add an allow-rule. Writing `.claude\commands\*.md` is agent-config self-modification
([[cannot-self-edit-permissions]]).
