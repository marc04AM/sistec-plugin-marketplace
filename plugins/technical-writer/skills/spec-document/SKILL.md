---
name: spec-document
description: Create a Sistec engineering-sheet specification / design document as a single self-contained HTML file — the paper/ink/signal styled sheet with light+dark theme toggle, an eyebrow + title + lede header, a signature block (Autore/Versione/Ultima revisione), numbered §sections, callouts (info/key/risk), SVG figure plates with legends, tokenized tables, status tags, numbered step lists, code/pseudo-code blocks, and a Revisions table. Use when the user asks to write, create, or draft a specification, design doc, technical spec, architecture writeup, or "documento di specifica" in the Sistec style, or references esempio.html / the shared engineering-sheet look.
---

# spec-document

Produce a specification document matching the Sistec engineering-sheet style: the exact CSS design
system (`--paper`/`--ink`/`--signal` tokens — warm terracotta accent `#cc785c` on cream `#f7f6f3`,
Cascadia + Segoe fonts, light/dark + theme toggle), structural chrome (`header.sheet`, `dl.sig`,
numbered `§` sections, `figure` plates, `.tbl-wrap` tables with accent-header cards, Revisions
table, footer), and Sistec conventions.

## Files in this skill

- `template.html` — the scaffold: full `<style>` block **verbatim** + a fillable body skeleton + the
  theme-toggle script. Start every document by copying this.
- `sheet.css` — the same CSS as `template.html`'s `<style>` block, kept as a standalone file so it can
  be diffed straight against the live site's `style.css` when the palette/style changes again. Not
  linked by generated docs (those stay single-file) — edit it **and** `template.html` together, in sync.
- `components.md` — copy-paste markup for every block (callout, figure/SVG, table, steps, pre, tags).
  Read it when you need a component you don't already have in front of you.

## Workflow

1. **Resolve author identity.** Read `%localappdata%\Sistec\SistecNode.xml`
   (`C:\Users\<user>\AppData\Local\Sistec\SistecNode.xml`) → `FullName`, `Team`, `Role`. Fill the
   `dl.sig` Autore line as `<b>FullName</b> · Team · Role` and "revisionato da FullName @Team".
   If the file is missing, create it with `FullName = "Unknown user"` and proceed — never block.
2. **Gather the spec content.** Establish: title, one-paragraph lede (the central guarantee/decision),
   the meta chips (2–4 key decisions/dates), the section list, and the design authority file (e.g.
   `<project>.design.md`) if one exists.
3. **Copy `template.html`** to the target path and fill placeholders:
   - `<title>` + `.eyebrow` + `<h1>` + `.lede` + `.meta` chips.
   - `dl.sig`: Autore (step 1), Versione `1.0` (new doc), Ultima revisione = today.
   - Intro paragraph.
4. **Write the sections.** One `<section>` per topic, `.sec-no` numbered `§1…§N` in order; sub-topics
   as `<h3>` with dotted numbers (`4.1`). Pull blocks from `components.md`. Lead each `§` with prose,
   then the supporting figure/table/steps.
5. **Diagrams.** Author SVG inline (`svg.dgm` in a `figure` plate). Fills/strokes MUST use token vars
   (`var(--signal)`, `var(--ok)`, …) so they theme — never hard-code hex in the body/SVG. Add a
   `.legend` mapping swatch → meaning.
6. **Revisions section** (`§` = `rev`, always last before footer) + **footer**. New doc = one `1.0`
   "Emissione iniziale" row. Footer restates `N § · M figure` and `v1.0`.
7. **Fill the footer** section/figure counts and version.

## Revising an existing doc (version bump)

When editing an already-issued sheet, do all four in the same change:
- add a **new top row** to the Revisions table (`1.x`, today, author, `<b>Titolo.</b>` + what changed);
- bump `dl.sig` **Versione** and **Ultima revisione**;
- bump the **footer** `v…` and, if changed, the `N § · M figure` count.

## Rules

- **Self-contained, single file.** All CSS inline in the `<style>` block; SVG inline; no external
  fonts/scripts/images. It must open correctly by double-click and also survive as a Claude Artifact.
- **Never touch the `<style>` block or the theme script** — they are the shared design system; copy
  verbatim from `template.html`. Style only via the existing classes/tokens. If the design system
  itself needs updating, edit `template.html` and `sheet.css` together (see "Files in this skill").
- **Dates** `YYYY-MM-DD`. **Language** matches the request (the reference is Italian).
- **Escape** `<`, `>`, `&` as `&lt;`/`&gt;`/`&amp;` inside `<pre>`/`<code>` content.
- **Save location:** default to `<project root>\specifications\<name>.html` when working inside a
  project; otherwise the path the user gives.
- Prefer showing structure with the right block: a *flow* → `ol.steps`; a *comparison/scenarios* →
  table with status tags; a *takeaway* → `.callout key`; an *open risk* → `.callout risk`; an
  *architecture* → `figure` + SVG.
