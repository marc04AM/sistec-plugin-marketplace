---
name: technical-writer
description: Generates from SCRATCH the operator manual of an HMI in Italian (Markdown → HTML) from the plant's control narratives, replicating the structure, tone and formatting of an example manual. Use it when the user wants to create, draft or write a NEW operator manual / HMI manual starting from control narratives, a section index and screenshots (e.g. "crea il manuale operatore", "redigi il manuale HMI", "scrivi il manuale"). To update, correct or revise an EXISTING Word .docx manual use the maintain-manual skill instead (not this one).
---

# Technical Writer — HMI operator manual

Drafts the **HMI operator manual** in **Italian**, drawing the content from the
plant's control narratives and replicating the structure, tone and conventions
of the example manual shipped with the plugin. The result is a Markdown manual with
image placeholders, then rendered to **HTML** with the bundled `style.css` stylesheet.
These instructions are in English, but the manual itself is always written in Italian.

## Golden rule
**Do not invent features.** Describe only what is documented in the control
narratives or visible in the screenshots. If a piece of information is missing, insert a
`<!-- TODO: ... -->` marker instead of imagining it. If two sources contradict each other,
do not pick one silently: mark the point with `<!-- TODO: conflitto ... -->` and ask.

## Plugin assets (form and style references)
These files live in the plugin, in `${CLAUDE_PLUGIN_ROOT}/assets/`. They are **only a
reference for form**: never copy their technical content verbatim.

| Asset | Role |
| --- | --- |
| `assets/exampleManual.md` | Example manual (Italian): model for structure, tone, symbols, ICONA/FUNZIONE tables, safety phrases, captions. |
| `assets/style.css` | Stylesheet for the final HTML rendering (headings, tables, captioned images, safety blocks, "sheet" layout). |
| `assets/manual-structure.template.md` | Template for the section index the user fills in. |
| `assets/img-README.md` | Image naming conventions. |

## Project inputs (what to read)
The inputs are not fixed: they change from project to project. Always read what is
actually present; do not assume file or section names.

| Source | Role |
| --- | --- |
| `docs/manual-structure.md` | **Index/outline** + section → control narrative mapping. Written by the user: it is the order of the sections to draft. If the project still has the legacy `docs/struttura-manuale.md` instead, use that. |
| `ControlNarrative/*.md` | **Content** (source of truth). The files present vary by project. |
| `src/img/` | Images/screenshots to insert into the manual. |

## Output (what to produce, at the project root)
1. `ManualeHMI.md` — the complete manual in Markdown.
2. `ManualeHMI.html` — HTML version: the `<body>` contains the manual rendered from
   Markdown, the `<head>` links the stylesheet with `<link rel="stylesheet" href="style.css">`.
   Image paths stay `src/img/...`.
3. `immagini-richieste.md` — list of the image placeholders still to be supplied,
   aligned with the placeholders in the manual. One line per placeholder:
   ```
   - [ ] src/img/<nome>.png — <didascalia> — sezione <X.Y>
   ```

If `ManualeHMI.md`/`.html` already exist, ask before overwriting them: a regeneration
would wipe out the manual edits made to the Markdown source.

## Workspace setup (if files are missing)
If the project is not set up yet, prepare the scaffolding by copying the assets:
- Create `docs/`, `ControlNarrative/`, `src/img/` if missing.
- If `docs/manual-structure.md` is missing (and there is no legacy `docs/struttura-manuale.md`), copy `${CLAUDE_PLUGIN_ROOT}/assets/manual-structure.template.md` to it.
- If `src/img/README.md` is missing, copy `${CLAUDE_PLUGIN_ROOT}/assets/img-README.md`.
- If `style.css` is missing at the root, copy `${CLAUDE_PLUGIN_ROOT}/assets/style.css`
  (it must sit next to `ManualeHMI.html` and `src/img/`, so the paths stay relative).

Then invite the user to: upload the images to `src/img/`, fill in the index in
`docs/manual-structure.md`, upload the control narratives to `ControlNarrative/`.

## Style conventions (for consistency with the example manual)
- **Language**: write the manual in Italian, impersonal form ("premere", "verificare", "selezionare").
- **Hierarchical numbering**: `1.`, `1.1.`, `1.1.1.`. UPPERCASE titles for the main chapters.
- **Images**: each image as
  ```
  ![<didascalia>](src/img/<nome>.png)

  *Immagine: <didascalia descrittiva>.*
  ```
- **Callouts on screenshots**: for numbered references on an image, use a numbered list below the image (e.g. `1. MENU LATERALE: ...`).
- **Descriptive lists**: bullets for descriptions; sub-bullets for details.
- **ICONA / FUNZIONE tables** (icon / function): to list icons and their function.
- **Safety**: safety prescriptions in a dedicated block before the procedures, prescriptive tone.
- **UI buttons/labels**: in guillemets «...» (e.g. «MANUALE», «SAFETY RESET», «Download»).
- **Terminology**: consistently use the terms introduced by the control narratives; keep a consistent glossary throughout the manual.

## Recommended workflow
1. Read `docs/manual-structure.md` (or the legacy `docs/struttura-manuale.md`) to get the index and, for each entry, the source control narrative.
2. Read all the `ControlNarrative/*.md` present and the actual listing of `src/img/`.
3. Consult `${CLAUDE_PLUGIN_ROOT}/assets/exampleManual.md` as a model of **form** (never of content).
4. Draft section by section following the index; for each section draw **only** on the indicated narrative. If the indicated narrative is missing or empty, insert `<!-- TODO: narrative mancante per <sezione> -->` and flag it in the report instead of proceeding blindly.
5. Insert the image placeholders where screenshots are needed; update `immagini-richieste.md`.
6. Check terminological consistency.
7. Mark every information gap with `<!-- TODO: ... -->`.
8. Generate `ManualeHMI.html` linking `style.css`.

## HTML rendering
Convert `ManualeHMI.md` to HTML preserving the structure (headings, captioned images, tables):
use a Markdown→HTML converter (e.g. pandoc) if available, otherwise render by hand following the
skeleton below. Minimal structure:
```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Manuale Operativo - Sistema HMI</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- manual content rendered from Markdown to HTML -->
</body>
</html>
```
- Keep `ManualeHMI.html` at the same level as `style.css` and `src/img/`.
- Do not duplicate the `style.css` rules inline.
- `ManualeHMI.md` remains the editable source; the HTML must be regenerated from it.
