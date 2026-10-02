---
name: translate
description: Generates the MySQL INSERT for the language_spv table from an HMI's MissingTranslations.csv. For each key it derives the StringName (exact, including any leading '#') and the Italian/English texts by reading the call site in the code, preserves string.Format placeholders, and writes an idempotent .sql ready to run. Use it when there is a MissingTranslations.csv to load into language_spv.
disable-model-invocation: true
---

# translate — MissingTranslations.csv → INSERT `language_spv`

Converts the missing translations logged by an HMI (`MissingTranslations.csv`) into a ready-to-run `.sql`:
an idempotent `INSERT` into the canonical `language_spv` table. **It only generates the file** — it does not
connect to the database; you run it yourself.

## 1. Resolve the CSV

- Path given → use it.
- No path → the **most recent** `MissingTranslations.csv` (by modification date) under the working
  folder (typically `**/bin/**/MissingTranslations.csv`). None found → report it and stop.
- Empty CSV or no data rows (0 keys) → report it and stop: do not generate an empty `INSERT`.

## 2. Parse → distinct keys

CSV columns (delimiter `;`, in this order): `Timestamp;Locale;Key;DefaultText;Module;Method`.
If a field contains `;` or quotes, handle standard CSV quoting (field in `"…"`, `""` as
escape) instead of splitting blindly. Collapse to **one row per distinct `Key`** (a key is
logged once per locale). If the same `Key` appears with **conflicting** `DefaultText` values, keep
the one with the most recent `Timestamp` and **report the conflict**. Keep `DefaultText`, `Module`,
`Method`: they point to the call site for Step 3.

## 3. Derive Italian + English from the call site (the core step)

For each key, `grep` the source at `Module`/`Method` (and the `GetOrDefault(key, default)` call)
to read the intended text and its meaning, then produce a clean **Italian** value and a clean **English**
value:

- the `DefaultText` without `#` is the author's fallback — usually right for one language; supply
  the natural translation for the other yourself;
- disambiguate from context (title vs body, column header, enum member, unit of measure);
- **preserve `string.Format` placeholders** (`{0}`, `{1}`, …) verbatim in both languages;
- **flag every guessed value** (no readable default in the code) so the user can check it;
- if the call site **cannot be found** (grep on `Module`/`Method` comes back empty), mark the key as *unresolved*,
  still emit the row with `DefaultText` as a flagged provisional value, and add it to the list in the report.

### Correctness rule #1 — `StringName` = exact key

The HMI resolves a term with an **exact dictionary hit, without stripping the `#`**. So
`StringName` **must** be the raw key: keys written with a leading `#` in the code
(`"#ProductionLog"`) are stored **with** the `#`; those without (`plc_PLC_0`) without it. Getting this wrong = the
term never resolves at runtime. The `#` in the CSV's `DefaultText` column, by contrast, is only the
"untranslated" marker — it is **not** part of the key.

## 4. Write the `.sql`

A single multi-row, **idempotent** `INSERT`, in **UTF-8** (accented IT text):

```sql
INSERT INTO language_spv (StringName, Italian, English) VALUES
  ('#ProductionLog', 'Log di produzione', 'Production log'),
  ('#JobSplit',      'Divisione lavoro {0}', 'Job split {0}')
ON DUPLICATE KEY UPDATE Italian = VALUES(Italian), English = VALUES(English);
```

- `StringName` = exact key (incl. `#`); leave `TimeStamp`/`Other` at their defaults.
- The `ON DUPLICATE KEY UPDATE … = VALUES(…)` tail makes the INSERT re-runnable without duplicate-key
  errors and works on **both MySQL 5.7 and 8.x** — no version detection.
- **Escape single quotes** in the texts (`'` → `''`, standard MySQL escaping): Italian is full of them (`l'operatore` → `l''operatore`).
- Comment header: source CSV, table, and the rules (exact key, `#` marker,
  idempotency). Group the tuples by area with one comment per group; mark with a comment the rows
  whose value is **guessed**.
- Default output: `<csv-dir>\MissingTranslations.sql` (or the given path). If the file already exists, warn before overwriting it.

## 5. Report

Path of the `.sql`, counts (distinct keys / guessed), the list of guessed values to vet, and
the command to run it:

```
mysql -h <host> -u <user> -p <db> --default-character-set=utf8mb4 < <out>
```
