# technical-writer

Sistec marketplace plugin for **technical documentation** in Italian, on three
fronts: **generating** a new HMI operator manual (Markdown → HTML) from the control narratives,
**maintaining** an existing Word (`.docx`) manual (revisions, copy-edit, audit vs code,
structure, comments) and **drafting** specification/design documents in the Sistec
engineering-sheet style (self-contained HTML).

The skill instructions are in English; the documents they produce are written in Italian.

## Components

| Component | File | What it does |
| :-------- | :--- | :----------- |
| Skill | `skills/technical-writer/SKILL.md` | **Generates** the manual (MD/HTML) from the control narratives; invocable as `/technical-writer:technical-writer` or automatically when you ask to create an HMI manual |
| Skill | `skills/maintain-manual/SKILL.md` | **Maintains** an existing Word (`.docx`) manual via python-docx: ports revisions (including hidden comments/tracked-changes), copy-edit, coverage audit vs code, structure fixes, review comments. Works on a versioned copy (master untouched) |
| Skill | `skills/spec-document/SKILL.md` | **Drafts** a specification/design document as a single self-contained HTML file in the Sistec engineering-sheet style (light/dark theme, § sections, callouts, SVG figures, Revisions table); invocable as `/technical-writer:spec-document` or automatically when you ask for a specification document |
| Asset | `skills/spec-document/template.html` | Document scaffold: design-system CSS + body skeleton + theme script |
| Asset | `skills/spec-document/sheet.css` | Same CSS as `template.html`, standalone for diffing against the site; keep in sync |
| Asset | `skills/spec-document/components.md` | Copy-paste markup for every block (callout, figure, tables, steps, tag) |
| Asset | `assets/exampleManual.md` | Example manual (Italian): a reference for **form**, not content |
| Asset | `assets/style.css` | Stylesheet for the final HTML rendering |
| Asset | `assets/manual-structure.template.md` | Template for the section index |
| Asset | `assets/img-README.md` | Image naming conventions |

## How it works

1. Prepare the project: images in `src/img/`, index in `docs/manual-structure.md`
   (a legacy `docs/struttura-manuale.md` is still read), control narratives in
   `ControlNarrative/`. The skill can create the scaffolding by copying the bundled templates.
2. Ask it to generate the manual.
3. The skill produces, at the project root:
   - `ManualeHMI.md` — the manual in Markdown,
   - `ManualeHMI.html` — the manual in HTML (links `style.css`),
   - `immagini-richieste.md` — image placeholders still to be supplied.

## Principles

- **Language**: the manual is written in Italian, impersonal form.
- **Source of truth**: the control narratives. Do not invent features; gaps
  are marked with `<!-- TODO: ... -->`.
- **Example = form, not content**: `exampleManual.md` is a model of structure
  and style; never copy its technical data.

## Quick test

```bash
claude --plugin-dir ./plugins/technical-writer
```

Then in the session:

```shell
/technical-writer:technical-writer
```
