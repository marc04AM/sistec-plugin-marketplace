---
name: technical-writer
description: Genera il manuale operatore di un'HMI in italiano a partire dalle control narrative dell'impianto, seguendo struttura, tono e formattazione di un manuale di esempio. Usala quando l'utente chiede di creare, redigere o aggiornare un manuale operatore / manuale HMI a partire da control narrative, indice delle sezioni e screenshot.
---

# Technical Writer — Manuale operatore HMI

Redige il **manuale operatore dell'HMI** in **italiano**, attingendo i contenuti
dalle control narrative dell'impianto e replicando struttura, tono e convenzioni
del manuale di esempio fornito con il plugin. L'esito è un manuale Markdown con
segnaposto immagine, reso poi in **HTML** con lo stile bundle `style.css`.

## Regola d'oro
**Non inventare funzionalità.** Descrivi solo ciò che è documentato nelle control
narrative o visibile negli screenshot. Se manca un'informazione, inserisci un
marcatore `<!-- TODO: ... -->` invece di immaginarla.

## Asset del plugin (riferimenti di forma e stile)
Questi file vivono nel plugin, in `${CLAUDE_PLUGIN_ROOT}/assets/`. Sono **solo
riferimento di forma**: non copiarne mai i contenuti tecnici alla lettera.

| Asset | Ruolo |
| --- | --- |
| `assets/exampleManual.md` | Manuale di esempio: modello di struttura, tono, simboli, tabelle ICONA/FUNZIONE, frasi di sicurezza, didascalie. |
| `assets/style.css` | Stile per la resa HTML finale (titoli, tabelle, immagini con didascalia, blocchi sicurezza, impaginazione "foglio"). |
| `assets/struttura-manuale.template.md` | Template dell'indice delle sezioni da far compilare all'utente. |
| `assets/img-README.md` | Convenzioni di denominazione delle immagini. |

## Input del progetto (cosa leggere)
Gli input non sono fissi: cambiano da progetto a progetto. Leggi sempre ciò che è
effettivamente presente, non assumere nomi di file o sezioni.

| Fonte | Ruolo |
| --- | --- |
| `docs/struttura-manuale.md` | **Indice/outline** + mappatura sezione → control narrative. Scritto dall'utente: è l'ordine delle sezioni da redigere. |
| `ControlNarrative/*.md` | **Contenuto** (fonte di verità). I file presenti variano per progetto. |
| `src/img/` | Immagini/screenshot da inserire nel manuale. |

## Output (cosa produrre, a livello root del progetto)
1. `ManualeHMI.md` — manuale completo in Markdown.
2. `ManualeHMI.html` — versione HTML: il `<body>` contiene il manuale reso da
   Markdown, l'`<head>` linka lo stile con `<link rel="stylesheet" href="style.css">`.
   I percorsi immagine restano `src/img/...`.
3. `immagini-richieste.md` — elenco dei segnaposto immagine ancora da fornire,
   allineato ai segnaposto presenti nel manuale.

## Setup del workspace (se mancano i file)
Se il progetto non è ancora predisposto, prepara lo scaffolding copiando gli asset:
- Crea `docs/`, `ControlNarrative/`, `src/img/` se assenti.
- Se manca `docs/struttura-manuale.md`, copia `${CLAUDE_PLUGIN_ROOT}/assets/struttura-manuale.template.md`.
- Se manca `src/img/README.md`, copia `${CLAUDE_PLUGIN_ROOT}/assets/img-README.md`.
- Se manca `style.css` a livello root, copia `${CLAUDE_PLUGIN_ROOT}/assets/style.css`
  (deve stare accanto a `ManualeHMI.html` e a `src/img/`, così i percorsi restano relativi).

Poi invita l'utente a: caricare le immagini in `src/img/`, compilare l'indice in
`docs/struttura-manuale.md`, caricare le control narrative in `ControlNarrative/`.

## Convenzioni di stile (obbligatorie)
- **Lingua**: italiano, forma impersonale ("premere", "verificare", "selezionare").
- **Numerazione gerarchica**: `1.`, `1.1.`, `1.1.1.`. Titoli in MAIUSCOLO per i capitoli principali.
- **Immagini**: ogni immagine come
  ```
  ![<didascalia>](src/img/<nome>.png)

  *Immagine: <didascalia descrittiva>.*
  ```
- **Callout su screenshot**: per riferimenti numerati su un'immagine, usa una lista numerata sotto l'immagine (es. `1. MENU LATERALE: ...`).
- **Elenchi descrittivi**: bullet per le descrizioni; sub-bullet per i dettagli.
- **Tabelle ICONA / FUNZIONE**: per elencare icone e relativa funzione.
- **Sicurezza**: prescrizioni di sicurezza in blocco dedicato prima delle procedure, tono prescrittivo.
- **Pulsanti/etichette UI**: tra virgolette caporali «...» (es. «MANUALE», «SAFETY RESET», «Download»).
- **Terminologia**: usa coerentemente i termini introdotti dalle control narrative; mantieni un glossario coerente per tutto il manuale.

## Workflow consigliato
1. Leggi `docs/struttura-manuale.md` per ottenere l'indice e, per ciascuna voce, la control narrative di origine.
2. Leggi tutte le `ControlNarrative/*.md` presenti e l'elenco effettivo di `src/img/`.
3. Consulta `${CLAUDE_PLUGIN_ROOT}/assets/exampleManual.md` come modello di **forma** (mai di contenuto).
4. Redigi sezione per sezione seguendo l'indice; per ogni sezione attingi **solo** alla narrative indicata.
5. Inserisci i segnaposto immagine dove servono screenshot; aggiorna `immagini-richieste.md`.
6. Verifica coerenza terminologica.
7. Marca con `<!-- TODO: ... -->` ogni lacuna informativa.
8. Genera `ManualeHMI.html` linkando `style.css`.

## Resa in HTML
Struttura minima:
```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Manuale Operativo - Sistema HMI</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- contenuto del manuale reso da Markdown a HTML -->
</body>
</html>
```
- Tieni `ManualeHMI.html` allo stesso livello di `style.css` e `src/img/`.
- Non duplicare le regole di `style.css` inline.
- `ManualeHMI.md` resta la sorgente editabile; l'HTML va rigenerato da quella.
