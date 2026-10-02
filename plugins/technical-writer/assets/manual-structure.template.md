# HMI Manual Structure

Index of the manual's sections, **filled in by the user** before asking
the agent to generate the manual. It is the order in which the sections will be written.
Section titles are written in Italian, as they appear in the manual.

## How to fill it in
- One row per section, with hierarchical numbering (`1`, `1.1`, `1.1.1`).
- **Section** column: title of the entry.
- **Source** column: the file in `ControlNarrative/` to draw the content from.
  - Use `src/img` if the section is based only on the images/screenshots.
  - Use `—` if the section is introductory or editorial.
  - Leave `TODO` if the source is not yet available.

> The agent follows this index in the given order and, for each entry, draws
> **only** on the specified source. Gaps are marked with `<!-- TODO: ... -->`.

## Index

| # | Section | Source |
| --- | --- | --- |
| 1 | PREMESSA | — |
|  |  |  |

<!--
Example of a filled-in index:

| # | Section | Source |
| --- | --- | --- |
| 1 | PREMESSA | — |
| 2 | COMANDI SOFTWARE | — |
| 2.1 | Autenticazione | AvvioSpegnimento.md |
| 3 | CONTROLLO DEL PANNELLO | src/img |
| 3.1 | Layout generale | src/img |
| 4 | RICETTA | Ricetta.md |
| 5 | AVVIO DELLA PRODUZIONE | AvvioSpegnimento.md |
-->
