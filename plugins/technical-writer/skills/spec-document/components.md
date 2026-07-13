# Component library — Sistec engineering-sheet

Copy-paste blocks. All colors reference CSS token vars (`var(--signal)`, `var(--ok)`, …) so every
component — SVG included — themes automatically in light/dark. Never hard-code hex in the body.

Token roles: `--signal` accent/primary, `--ok` good/safe, `--warn` caution, `--crit` risk/error,
`--ink`/`--ink-soft`/`--slate` text hierarchy, `--surface`/`--surface-2` panel fills, `--line`/`--line-strong` borders.

---

## Section header (numbered)

```html
<section>
  <div class="sec-head"><span class="sec-no">§3</span><h2>Titolo</h2></div>
  <p>Testo.</p>
  <h3>3.1 Sotto-sezione</h3>
  <p>Testo.</p>
</section>
```

`.sec-no` = `§1`, `§2`, … in order; the Revisions section uses `rev`. Sub-sections use `<h3>` with a
dotted number (`3.1`, `3.2`).

## Inline marks

```html
<code>token</code>            <!-- monospace inline literal -->
<span class="kbd">/share</span>   <!-- command / keystroke -->
<strong>emphasis</strong>  <em>italic</em>
```

## Callouts

```html
<div class="callout"><h4>TITOLO NEUTRO</h4><p>Nota informativa.</p></div>
<div class="callout key"><h4>IL PUNTO CENTRALE</h4><p>Garanzia/risultato positivo.</p></div>
<div class="callout risk"><h4>RISCHIO / DA MONITORARE</h4><p>Modalità di guasto o punto aperto.</p></div>
```

`.callout` = signal (info), `.key` = ok/green (the central takeaway), `.risk` = crit/red (danger/open issue).

## Table

```html
<div class="tbl-wrap"><table>
  <thead><tr><th>Colonna</th><th>Colonna</th></tr></thead>
  <tbody>
    <tr><td>cella</td><td class="col-mono">valore monospace</td></tr>
  </tbody>
</table></div>
```

`.col-mono` on a `<td>` for numeric/code-ish cells. Always wrap in `.tbl-wrap` (horizontal scroll on narrow).

## Status tags (inside cells or text)

```html
<span class="tag t-ok">sicuro</span>
<span class="tag t-warn">limitato</span>
<span class="tag t-bad">rotto</span>
```

## Numbered steps (flow / procedure)

```html
<ol class="steps">
  <li><b>Passo.</b> Descrizione con <code>dettagli</code>.</li>
  <li><b>Passo.</b> …</li>
</ol>
```

## Tight bullet list

```html
<ul class="tight">
  <li><b>Voce.</b> testo</li>
</ul>
```

## Code / pseudo-code block

```html
<pre><b>KEYWORD</b>  intestazione
  riga di codice
  if x &gt; y:                <span class="c">// commento</span>
      <b class="crit">STOP — condizione critica</b></pre>
```

`<b>` = signal keyword, `<span class="c">` = muted comment, `<b class="crit">` = red critical line.
Escape `<`, `>`, `&` as `&lt;`, `&gt;`, `&amp;`.

## Figure plate with SVG diagram

```html
<figure>
  <div class="plate-cap"><b>Fig 1</b><span>Didascalia: cosa mostra il diagramma.</span></div>
  <div class="plate-body">
    <svg class="dgm" viewBox="0 0 920 480" role="img" aria-label="Descrizione">
      <defs>
        <marker id="ar" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
          <path d="M0,0 L8,3 L0,6 Z" fill="var(--slate)"/></marker>
      </defs>
      <rect x="86" y="66" width="220" height="120" rx="10"
            fill="var(--signal)" fill-opacity="0.12" stroke="var(--signal)"/>
      <text x="196" y="92" text-anchor="middle" font-size="14" font-weight="700"
            fill="var(--signal-ink)">Blocco</text>
      <text x="196" y="114" text-anchor="middle" font-size="11.5" fill="var(--slate)">sottotitolo</text>
      <line x1="306" y1="126" x2="420" y2="126" stroke="var(--signal)" stroke-width="2"
            marker-end="url(#ar)"/>
    </svg>
  </div>
  <div class="legend">
    <span><i class="sw" style="background:var(--signal);border-color:var(--signal)"></i> categoria</span>
    <span><i class="sw" style="background:var(--ok);border-color:var(--ok)"></i> categoria</span>
  </div>
</figure>
```

SVG rules:
- `viewBox` with `class="dgm"` — scales responsively; keep `min-width` handled by CSS (620px).
- Fills/strokes = token vars; boxes use `fill-opacity="0.10"–"0.16"` washes over a solid `stroke`.
- One `<marker>` per arrow color (`--slate` neutral, `--signal`, `--ok`). Reuse via `marker-end="url(#id)"`.
- Label boxes with `<text text-anchor="middle">`; keep a `.legend` under the plate mapping swatch → meaning.

## Revisions table (always the final section)

```html
<section>
  <div class="sec-head"><span class="sec-no">rev</span><h2>Revisioni</h2></div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Versione</th><th>Data</th><th>Revisionato da</th><th>Modifiche introdotte</th></tr></thead>
    <tbody>
      <tr><td class="col-mono">1.1</td><td class="col-mono">YYYY-MM-DD</td><td>FULLNAME @TEAM</td>
        <td><b>Titolo modifica.</b> Cosa è cambiato.</td></tr>
      <tr><td class="col-mono">1.0</td><td class="col-mono">YYYY-MM-DD</td><td>FULLNAME @TEAM</td>
        <td><b>Emissione iniziale.</b> …</td></tr>
    </tbody>
  </table></div>
</section>
```

Newest revision on top. Every version bump adds a row here AND updates `dl.sig` Versione + Ultima revisione + the footer `v…`.
