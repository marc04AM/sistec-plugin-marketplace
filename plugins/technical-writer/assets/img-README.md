# src/img/ — immagini del manuale

Cartella delle immagini/screenshot da inserire nel manuale.

## Convenzione di denominazione
Nominare i file in modo descrittivo e stabile, così che i segnaposto nel manuale
non cambino quando l'immagine viene fornita:

```
<sezione>-<soggetto>.png
```

Esempi:
- `2.2-login.png` — finestra di accesso utente.
- `3.1-layout-generale.png` — layout generale del pannello.
- `3.2-menu-laterale.png` — menu laterale.
- `4-ricetta-pagina.png` — pagina Ricetta.
- `5-home-taskboard.png` — pagina HOME con task list.
- `7.1-palletstateview.png` — indicatore baia di scarico.
- `8.3-diagnostica-avvio.png` — finestra controlli di avvio.

## Riferimento nel manuale
Nei file Markdown l'immagine si inserisce come:

```markdown
![menu laterale](src/img/3.2-menu-laterale.png)
*Immagine: Menu laterale dell'HMI.*
```

Il testo `alt` (`![...]`) viene reso da `style.css` come didascalia sotto l'immagine.

## Stato immagini
L'elenco dei segnaposto ancora privi di immagine è mantenuto in
`immagini-richieste.md` (a livello root).
